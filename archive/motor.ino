/* Copyright (C) 2021 Sean D'Epagnier <seandepagnier@gmail.com>
 *
 * This Program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public
 * License as published by the Free Software Foundation; either
 * version 3 of the License, or (at your option) any later version.


This program is meant to interface with pwm based
motor controller either brushless or brushed, or a regular RC servo

You may need to modify the source code to support different hardware

adc pin0 is a resistor divider to measure voltage
             allowing up to 20 volts (10k and 560 ohm, 1.1 volt reference)
adc pin1 goes to .01/.05 ohm shunt to measure current
adc pin2 goes to 100k resistor to 5v and 10k NTC thermistor to gnd ctrl temp
adc pin3 goes to 100k resistor to 5v and 10k NTC thermistor to gnd motor temp
adc pin4 rudder sense
unused analog pins should be grounded

digital pins 4 and 5 determine the current sense as folows:
pin 4 determines range
pin 5 determines high/low current  (20A or 60A max)

D4  D5
 1   1        .05 ohm, (or .001 ohm x 50 gain)
 0   1        .01 ohm
 1   0        .0005 ohm x 50 gain
 0   0        .00025 ohm x 200 gain   *ratiometric mode


digital pin6 is only read if VNH2SP30 is NOT defined. It determines:
1 - RC pwm:
   digital pin9 pwm output standard Electronic Speed Controller (ESC) (1-2 ms pulse every 20 ms)
           pin2 ESC programming input/output (with arduinousblinker script)
0 - Hbridge
   digital pin2 and pin3 for low side, pin9 and pin10 for high side


optional:digital pin7 forward fault for optional switch to stop forward travel. LOW for fault. HIGH for OK.
digital pin8 reverse fault for optional switch to stop reverse travel. LOW for fault. HIGH for OK.


Ratiometric Mode:
for D4=0 and D5=0, the adc operates over the 0-5 volt range
making it ratiometric (linearly accurate) for rudder feedback
and reduces impedance in the rudder measurement
the temperature resistors are changed to 10k and 10k ntc
voltage measurement accuracy is reduced, and the resistors used are
15k and 100k for a range of 38 volts.   Pin 12 is not used in this mode.


Pin 11 drives mosfet (560ohm and 10k resistors) for clutch engage.

If Pin 12 has 560 ohm resistor to A0, then 24 volts is supported,
this allows for measuring voltage up to 40.4 volts

D12
 1    0-20.75 volts (560 and 10k resistor)  resolution 0.02 volts
 0    0-40.4  volts (280 and 10k resistor)  resolution 0.04 volts

digital pin13 is led on when engaged


The program uses a simple protocol to ensure only
correct data can be received and to ensure that
false/incorrect or random data is very unlikely to
produce motor movement.

The input and output over uart has 4 byte packets

The first byte is the command or register, the next
two bytes is a 16bit value (signed or unsigned)
the last byte is a crc8 of the first 3 bytes

If incoming data has the correct crc for a few frames
the command can be recognized.

*/

/* vnh2sp30 is supported, but warning, I received 3 boards:
1) reverse is half power making chip very hot
2) reverse does not work
3) current sense does not work

3 out of 3 were defective, I do not recommend.

vnh2sp30  <->  arduino <->  CPC5001
+5V              5v
GND              GND
EN               D10
CS               A1
INA              D2
INB              D3
PWM              D9

If used with optical isolation (strongly recommended)
PWR+             VIN
                 5v         vcc
                 tx         rx
                 rx         tx
                 gnd        gnd
*/



/*
================================================================================
NOTES:

* See document on reading analog pins:  http://garretlab.web.fc2.com/en/arduino/inside/hardware/arduino/avr/cores/arduino/wiring_analog.c/analogRead.html
* See chip data sheet: https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-7810-Automotive-Microcontrollers-ATmega328P_Datasheet.pdf

REGISTER: ADMUX - Analog/Digital Multiplexer Selection Registers
MUX0 (bit 0), MUX1, MUX2, MUX3, ADLAR, REFS0, REFS1 (bit 7) are all bits in the ADMUX register. 
REFS1  REFS0   Means 
 0       0     Voltage applied to AREF pin
 0       1     Default reference voltage (5v for Uno)
 1       0     Reserved
 1       1     Internal reference voltage (1.1v for Uno)

MUX0 - MUX3 selects the analog pin:  
MUX3 MUX2 MUX1 MUX0  Pin
 0    0    0    0    0
 0    0    0    1    1
 0    0    1    0    2
 0    0    1    1    3
 0    1    0    0    4
 0    1    0    1    5
 0    1    1    0    6
 1    0    0    0    7 = DISABLED BY ARDUINO SOFTWARE - reads internal temp sensor.

REGISTER: ADCSRA 
This is the ADC Control and Status Register A.  It is used to control Analog/digital conversion. 
Bit names (7 to 0) are: ADEN, ADCS, ADATE, ADIF, ADIE, ADPS2, ADPS1, ADPS0.
Setting ADEN to 1 enables AD conversion. It is set in init(), which is called from main().
Setting ADSC to 1 starts AD conversion.  While AD is executing, this bit is 1. After completing conversion, it goes to 0.
ADATE enables automatic trigger of convresion.
ADIF (ADC Interrupt Flag) and ADIE (ADC Interrupt Enable) control interruption. Not used by Arduino software.
ADPS are used to determine the division factor between the system clock frequency and the input clock to the AD converter.

REGISTER: ADCH and ADCL
These are the registers to store the results of AD conversions.  Results The ADLAR of the ADMUX register controls how the result is stored.
Arduino sets this to 0, which means that the first two bits of the conversion result are stored in ADXH (ADCH?), and
the remaining 8 bits are stored in ADXL (ADCL?).


*/

#include <Arduino.h>
#include <stdint.h>
#include <stdarg.h>
#include <HardwareSerial.h>

#include <avr/wdt.h>
#include <avr/sleep.h>
#include <avr/boot.h>
#include <avr/eeprom.h>
#include <avr/pgmspace.h>
#include <util/delay.h>
#include "crc.h"

//#define VNH2SP30 // defined if this board is used
//#define DISABLE_TEMP_SENSE    // if no temp sensors avoid errors
//#define DISABLE_VOLTAGE_SENSE // if no voltage sense
//#define DISABLE_RUDDER_SENSE  // if no rudder sense


// run at 4mhz instead of 16mhz to save power
// and somehow at slower clock atmega328 is able to measure lower current from the shunt

#define DIV_CLOCK 2  // speed board runs at  1 for 16mhz, 2 for 8mhz, 4 for 4mhz (recommended 4 or 8mhz)
//#define BLINK  // blink status led while detached to avoid quiecent consumption of on led (3mA)
#define MAX_TIMER_TICKS 78

static volatile uint8_t timer1_state;

// 1.5uS
#define dead_time4 \
    asm volatile ("nop"); \
    asm volatile ("nop"); \
    asm volatile ("nop"); \
    asm volatile ("nop"); \
    asm volatile ("nop"); \
    asm volatile ("nop");

#if DIV_CLOCK==4
#define dead_time dead_time4
#elif DIV_CLOCK==2
#define dead_time \
    dead_time4 \
    dead_time4
#elif DIV_CLOCK==1
#define dead_time \
    dead_time4 \
    dead_time4 \
    dead_time4 \
    dead_time4
#warning "DIV_CLOCK set to 1, this will only work with 16mhz xtal"
#else
#error "invalid DIV_CLOCK"
#endif


// time to charge bootstrap capacitor twice dead time
#define charge_time \
        dead_time; \
        dead_time;

#define shunt_sense_pin 4 // use pin 4 to specify shunt resistance
uint8_t shunt_resistance = 1;

#define low_current_pin 5 // use pin 5 to specify low current (no amplifier)
uint8_t low_current = 1;

#define ratiometric_mode (!shunt_resistance && !low_current)

#define pwm_style_pin 6
// pwm style, 0 = hbridge, 1 = rc pwm, 2 = vnh2sp30, 3 = atmega328pb
#define PWM_STYLE_HBRIDGE 0
#define PWM_STYLE_RC 1
#define PWM_STYLE_VNH2SP30 2
#define PWM_STYLE_HBRIDGE_ATMEGA328PB 3
uint8_t pwm_style = PWM_STYLE_VNH2SP30;

#define port_fault_pin 7 // use pin 7 for optional fault. HIGH = no fault. LOW = fault
#define starboard_fault_pin 8 // use pin 8 for optional fault. HIGH = no fault. LOW = fault
// if switches pull this pin low, the motor is disengaged
// and will be noticed by the control program

#define pwm_output_pin 9

#define hbridge_a_bottom_pin 2
#define hbridge_b_bottom_pin 3
#define hbridge_a_top_pin 9
#define hbridge_b_top_pin 10
#define enable_pin 10 // for vnh2sp30

// for direct mosfet mode, define how to turn on/off mosfets
// do not use digitalWrite!
// PORTD maps to Arduino digital pins 0 to 7
//
//    DDRD - The Port D Data Direction Register - read/write
//    PORTD - The Port D Data Register - read/write
//    PIND - The Port D Input Pins Register - read only 
//
//PORTB maps to Arduino digital pins 8 to 13 The two high bits (6 & 7) map to the crystal pins and are not usable
//
//    DDRB - The Port B Data Direction Register - read/write
//    PORTB - The Port B Data Register - read/write
//    PINB - The Port B Input Pins Register - read only 
//
//PORTC maps to Arduino analog pins 0 to 5. Pins 6 & 7 are only accessible on the Arduino Mini
//
//    DDRC - The Port C Data Direction Register - read/write
//    PORTC - The Port C Data Register - read/write
//    PINC - The Port C Input Pins Register - read only 
#define a_top_on  PORTB |= _BV(PB1)
#define a_top_off PORTB &= ~_BV(PB1)
#define a_bottom_on PORTD |= _BV(PD2)
#define a_bottom_off PORTD &= ~_BV(PD2)
#define b_top_on  PORTB |= _BV(PB2)
#define b_top_off PORTB &= ~_BV(PB2)
#define b_bottom_on PORTD |= _BV(PD3)
#define b_bottom_off PORTD &= ~_BV(PD3)

#define clutch_pin 11 // use pin 11 to engage clutch
#define clutch_sense_pwm_pin A5

//#define clutch_on PORTB |= _BV(PB3)
//#define clutch_off PORTB &= ~_BV(PB3)
uint8_t clutch_pwm = 192, clutch_start_time;
uint8_t use_brake = 0, brake_on = 0; // brake when stopped

#define USE_ADC_ISR 0 // set to 1 to use interrupt (recommend 0)

#define voltage_sense_pin 12
#define VOLTAGE_MODE_12V 0
#define VOLTAGE_MODE_24V 1
uint8_t voltage_sense = HIGH;
uint8_t voltage_mode = VOLTAGE_MODE_12V;
uint16_t max_voltage = 1600; // 16 volts max in 12 volt mode

#define led_pin 13 // led is on when engaged

void debug(const char *fmt, ... ){
    char buf[128]; // resulting string limited to 128 chars
    va_list args;
    va_start (args, fmt );
    vsnprintf(buf, 128, fmt, args);
    va_end (args);
    Serial.print(buf);
}

// Port rudder > 1000.  Starboard rudder < 1000
#define NEUTRAL_RUDDER 1000
enum commands {
   COMMAND_CODE=0xc7,
   RESET_CODE=0xe7,
   MAX_CURRENT_CODE=0x1e,
   MAX_CONTROLLER_TEMP_CODE=0xa4,
   MAX_MOTOR_TEMP_CODE=0x5a,
   RUDDER_RANGE_CODE=0xb6,
   RUDDER_MIN_CODE=0x2b,
   RUDDER_MAX_CODE=0x4d,
   REPROGRAM_CODE=0x19,
   DISENGAGE_CODE=0x68,
   MAX_SLEW_CODE=0x71,
   EEPROM_READ_CODE=0x91,
   EEPROM_WRITE_CODE=0x53,
   CLUTCH_PWM_AND_BRAKE_CODE=0x36};

enum results {
   CURRENT_CODE=0x1c,
   VOLTAGE_CODE=0xb3,
   CONTROLLER_TEMP_CODE=0xf9,
   MOTOR_TEMP_CODE=0x48,
   RUDDER_SENSE_CODE=0xa7,
   FLAGS_CODE=0x8f,
   EEPROM_VALUE_CODE=0x9a};

enum {
   SYNC=1, // Bit 0
   OVERTEMP_FAULT=2, // Bit 1
   OVERCURRENT_FAULT=4, // Bit 2
   ENGAGED=8, // Bit 3
   INVALID=16, // Bit 4
   PORT_PIN_FAULT=32, // Bit 5
   STARBOARD_PIN_FAULT=64, // Bit 6
   BADVOLTAGE_FAULT=128, // Bit 7
   MIN_RUDDER_FAULT=256, // Bit 8
   MAX_RUDDER_FAULT=512, // Bit 9
   CURRENT_RANGE=1024, // Bit 10
   BAD_FUSES=2048, // Bit 11
   /* PORT_FAULT=4096  // Bit 12
   STARBOARD_FAULT=8192 // Bit 13
   ??? */ // Bit 14
   REBOOTED=32768}; // Bit 15

uint16_t flags = REBOOTED, faults = 0;
uint8_t serialin;

// we need these to be atomic for 16 bytes

uint16_t eeprom_read_16(int address)
{
    // ensure atomic update of 16 bits with 3 banks
    uint16_t v[3];
    for (int i=0; i<3; i++) {
        int addr = i*256 + address;
        v[i] = eeprom_read_word((uint16_t*)addr);
        //eeprom_read_byte((unsigned char *)addr) | eeprom_read_byte((unsigned char *)addr+1)<<8;
    }

    if (v[1] == v[2])
        return v[2];

    return v[0];
}

void eeprom_update_16(int address, uint16_t value)
{
    // write in 3 locations
    for (int i=0; i<3; i++) {
        int addr = i*256 + address;
        eeprom_update_word((uint16_t*)addr, value);
    }
}

uint8_t eeprom_read_8(int address, uint8_t &value)
{
    static uint8_t lastvalue, lastaddress=255;
    if (address & 1) { // odd
        if (address == lastaddress+1) {
            value = lastvalue;
            return 1;
        } else
            return 0;
    }

    // even
    uint16_t v = eeprom_read_16(address);
    value = v&0xff;
    lastvalue = v >> 8;
    lastaddress = address;
    return 1;
}

void eeprom_update_8(int address, uint8_t value)
{
    static uint8_t lastvalue, lastaddress=255;
    if (address & 1) { // odd
        if (address == lastaddress+1)
            eeprom_update_16(lastaddress, lastvalue | value<<8);
    } else {
        lastvalue = value;
        lastaddress = address;
    }
}

uint16_t max_current = 2000; // 20 Amps
uint16_t max_controller_temp= 7000; // 70C
uint16_t max_motor_temp = 7000; // 70C
uint8_t max_slew_speed = 50, max_slew_slow = 75; // 200 is full power in 1/10th of a second
uint16_t rudder_min = 0, rudder_max = 65535;

uint8_t eeprom_read_addr = 0;
uint8_t eeprom_read_end = 0;

uint8_t adcref = _BV(REFS0)| _BV(REFS1); // 1.1v
volatile uint8_t calculated_clock = 0; // must be volatile to work correctly
uint8_t timeout;
uint16_t serial_data_timeout;

void setup()
{
    PCICR = 0;
    PCMSK2 = 0;
        
    cli(); // disable interrupts
    CLKPR = _BV(CLKPCE);
    CLKPR = _BV(CLKPS1); // divide clock by 4
    /* Clear MCU Status Register. */
    MCUSR = 0;

    // set watchdog interrupt 16 ms to detect the clock speed (support 8mhz or 16mhz crystal)
    wdt_reset();
    WDTCSR = (1<<WDCE)|(1<<WDE);
    WDTCSR = (1<<WDIE);
    sei();

    uint32_t start = micros();
    while(!calculated_clock);  // wait for watchdog to fire
    uint16_t clock_time = micros() - start;
    uint8_t div_board = 1; // 1 for 16mhz
    if (clock_time < 2900) // 1800-2600 is 8mhz, 3800-4600 is 16mhz
        div_board = 2; // detected 8mhz crystal, otherwise assume 16mhz

    // after timing the clock frequency set the correct divider
    uint8_t div_clock = DIV_CLOCK/div_board;
    if (div_clock==4) {
        cli();
        CLKPR = _BV(CLKPCE);
        CLKPR = _BV(CLKPS1); // divide by 4
        sei();
    } else if (div_clock == 2) {
        cli();
        CLKPR = _BV(CLKPCE);
        CLKPR = _BV(CLKPS0); // divide by 2
        sei();
    } else {
        cli();
        CLKPR = _BV(CLKPCE);
        CLKPR = 0; // divide by 1
        sei();
    }

    // Disable all interrupts
    cli();

    // set watchdog to interrupt in 1/4th second
    WDTCSR = (1<<WDCE)|(1<<WDE);
    WDTCSR = (1<<WDIE) | (1<<WDP2);

    // read fuses, and report this as flag if they are wrong
    uint8_t lowBits      = boot_lock_fuse_bits_get(GET_LOW_FUSE_BITS);
    uint8_t highBits     = boot_lock_fuse_bits_get(GET_HIGH_FUSE_BITS);
    uint8_t extendedBits = boot_lock_fuse_bits_get(GET_EXTENDED_FUSE_BITS);
    // uint8_t lockBits     = boot_lock_fuse_bits_get(GET_LOCK_BITS); // too many clones don't set lock bits and there is no spm
    if ((lowBits != 0xFF && lowBits != 0x7F) ||
       (highBits != 0xda && highBits != 0xde) ||
       ((extendedBits&0xF6) != 0xF4)
       // || lockBits != 0xCF // too many clones don't set lock bits and there is no spm
        )
        flags |= BAD_FUSES;

    sei(); // Enable all interrupts.

    // enable pullup on unused pins (saves .5 mA)
    pinMode(A4, INPUT);
    digitalWrite(A4, LOW);

    pinMode(shunt_sense_pin, INPUT_PULLUP);
    pinMode(low_current_pin, INPUT_PULLUP);
    pinMode(pwm_style_pin, INPUT_PULLUP);
    pinMode(clutch_pin, INPUT_PULLUP);
    pinMode(voltage_sense_pin, INPUT_PULLUP);
    pinMode(clutch_sense_pwm_pin, INPUT_PULLUP);

    serialin = 0;
    // set up Serial library
    Serial.begin(38400*DIV_CLOCK);

    digitalWrite(A0, LOW);
    pinMode(A0, OUTPUT);
    voltage_sense = digitalRead(voltage_sense_pin);
    if (voltage_sense == LOW)
        pinMode(voltage_sense_pin, INPUT); // if attached, turn off pullup
    pinMode(A0, INPUT);


    digitalWrite(clutch_pin, LOW);
    pinMode(clutch_pin, OUTPUT); // clutch

    digitalWrite(led_pin, LOW);
    pinMode(led_pin, OUTPUT); // status LED

    pinMode(port_fault_pin, INPUT);
    digitalWrite(port_fault_pin, HIGH); /* enable internal pullups */
    pinMode(starboard_fault_pin, INPUT);
    digitalWrite(starboard_fault_pin, HIGH); /* enable internal pullups */

    pinMode(pwm_style_pin, INPUT);
    digitalWrite(pwm_style_pin, HIGH); /* enable internal pullups */

    pinMode(shunt_sense_pin, INPUT);
    digitalWrite(shunt_sense_pin, HIGH); /* enable internal pullups */

    pinMode(low_current_pin, INPUT);
    digitalWrite(low_current_pin, HIGH); /* enable internal pullups */

    _delay_us(100); // time to settle

    // test output type, pwm or h-bridge
#ifndef VNH2SP30
    pwm_style = digitalRead(pwm_style_pin);
#endif
    if (pwm_style != PWM_STYLE_HBRIDGE) {
        digitalWrite(pwm_output_pin, LOW); /* enable internal pullups */
        pinMode(pwm_output_pin, OUTPUT);
    }

#if defined(__AVR_ATmega328pb__)
    // read device signature bytes to identify processor
    uint8_t sig[3], c = 0;
    for (uint8_t i = 0; i < 5; i += 2)
        sig[c++] = Serial.print(boot_signature_byte_get(i));
//    if (0/*disable for now*/   &&   sig[0] == 0x1e && sig[1] == 0x95 && sig[2] == 0x16) {
//        // detected atmega328pb processor, we have timers 3 and 4 with hardware pwm possible
//        if (pwm_style == PWM_STYLE_HBRIDGE) {
//            // upgrade to use hardware pwm (style 3)
//            pwm_style = PWM_STYLE_HBRIDGE_ATMEGA328PB;
//            // use timers 1, 2, 3 for pwm (with deadtime)
//            // use timer 4 in place of timer 2 for count
//            // stop all timers
//            GTCCR = (1<<TSM)|(1<<PSRASY)|(1<<PSRSYNC); // halt all timers
//            ICR1 = 0x255; // use timer1 as 8 bit timer
//            ICR4 = 0x255; // use timer2 also as 8 bit timer
//            TCNT1 = 0;
//            TCNT2 = 10; // deadtime
//            TCNT3 = 10;
//            GTCCR = 0; // restart timers
//        }
//    }
#endif    
    
    // test shunt type, if pin wired to ground, we have 0.01 ohm, otherwise 0.05 ohm
    shunt_resistance = digitalRead(shunt_sense_pin);

    // test current
    low_current = digitalRead(low_current_pin);
    if (!low_current)
        max_current = 4000; // default start at 40 amps

    // setup adc
    DIDR0 = 0x1f; // disable digital io on analog pins
    if (ratiometric_mode) {
        adcref = _BV(REFS0); // 5v
        voltage_mode = VOLTAGE_MODE_24V; // 24v mode
        max_voltage = 3200; // increase max voltage to 32v
    } else
        adcref = _BV(REFS0)| _BV(REFS1); // 1.1v
    ADMUX = adcref | _BV(MUX0);
#if USE_ADC_ISR
    ADCSRA = _BV(ADEN) | _BV(ADIE); // enable adc with interrupts
#else
    ADCSRA = _BV(ADEN); // enable adc
#endif
    ADCSRA |= _BV(ADPS0) |  _BV(ADPS1) | _BV(ADPS2); // divide clock by 128
    ADCSRA |= _BV(ADSC); // start conversion

    timeout = 0;
#if defined(__AVR_ATmega328pb__)
    if (pwm_style == PWM_STYLE_HBRIDGE_ATMEGA328PB) {
        TCNT4 = 0;
        /// fix this TCCR4B = _BV(CS22) | _BV(CS21) | _BV(CS20); // divide 1024
        // use timer5 as timeout
    } else
#endif        
    {
        // use timer0 as timeout
        TCNT0 = 0;
        TCCR0A = 0;
        TCCR0B = _BV(CS02) | _BV(CS00); // divide 1024
    }
    serial_data_timeout = 250;
}

uint8_t in_bytes[3];
uint8_t sync_b = 0, in_sync_count = 0;

uint8_t byte_to_write_idx = 0, serial_command_to_output_idx = 0;
uint8_t crcbytes[3];

uint8_t rudder_sense = 0;

// command is from 0 to 2000 with 1000 being neutral
// Sets global variable 'actual_rudder_value'.
uint16_t actual_rudder_value = NEUTRAL_RUDDER;
void adjust_rudder_position(uint16_t value)
{
    actual_rudder_value = value;
    if (pwm_style == PWM_STYLE_RC)
//        OCR1A = 1200/DIV_CLOCK + value * 6 / 5 / DIV_CLOCK;
        OCR1A = 1500/DIV_CLOCK + value * 3 / 2 / DIV_CLOCK;
    //OCR1A = 1350/DIV_CLOCK + value * 27 / 20 / DIV_CLOCK;
    else if (pwm_style == PWM_STYLE_VNH2SP30) {
        OCR1A = abs((int)value - 1000) * 16 / DIV_CLOCK;
        if (value > 1040) {
            a_bottom_off;
            b_bottom_on;
        } else if (value < 960) {
            b_bottom_off;
            a_bottom_on;
        } else { // low, set pwm for brake (implement brake here?)
            a_bottom_off;
            b_bottom_off;
        }            
    } else {
        uint16_t OCR1A_u = 16000, OCR1B_u = 16000, ICR1_u = 1000;
        // use 62.5 hz at full power to reduce losses
        // some cycling is required to refresh the bootstrap capacitor
        // but the current through the motor remains continuous
        if (value > 1100) {
            if (value > 1900) {
                ICR1_u=64000;  //fPWM=62.5hz, 125hz, or 250hz
                timer1_state = 4; // take advantage of special state
                TIMSK1 = _BV(TOIE1);
            } else {
                ICR1_u=1000/DIV_CLOCK;  //fPWM=16khz
                OCR1A_u = 30 + (1900 - value)/DIV_CLOCK; // 30 is minimum time for interrupts to complete
                timer1_state = 1;
                TIMSK1 = _BV(TOIE1) | _BV(OCIE1A);
            }

        } else if (value < 900) {
            if (value < 100) {
                ICR1_u=64000;  //fPWM=62.5hz, 125hz, or 250hz
                timer1_state = 8; // take advantage of special state
                TIMSK1 = _BV(TOIE1);
            } else {
                ICR1_u=1000/DIV_CLOCK;  //fPWM=16khz
                OCR1B_u = 30 + (value-100)/DIV_CLOCK;
                timer1_state = 2;
                TIMSK1 = _BV(TOIE1) | _BV(OCIE1B);
            }
        } else {
            timer1_state = 0;
            TIMSK1 = 0;
            a_top_off;
            b_top_off;
            dead_time;
            if (brake_on) {
                a_bottom_on;  // set brake
                b_bottom_on;
            } else {
                a_bottom_off;
                b_bottom_off;
            }
        }

        if (TIMSK1) { // timer has interrupts, update registers
            OCR1A = OCR1A_u;
            OCR1B = OCR1B_u;
            if (ICR1 != ICR1_u) { // if frequency changed
                cli();
                ICR1 = ICR1_u;
                TCNT1 = ICR1_u - 40; // ensure timer is before new end
                sei();
            }
        }
    }
}


// Update the "actual_rudder_value", based on the commanded rudder value.
// Uses global vars commanded_rudder_value and actual_rudder_value.
// Sets global vars:
// * actual_rudder_value
void update_command()
{
    int16_t speed_rate = max_slew_speed;
    int16_t slow_rate = max_slew_slow; // value of 20 is 1 second full range at 50hz

    // uint16_t cur_value = OCR1A * 2 / 3 - NEUTRAL_RUDDER; // <-- This is old commented-out-code. If used, use cur_value for rudder_delta calculation.
    int16_t rudder_delta = (int)commanded_rudder_value - (int)actual_rudder_value;

    // limit motor speed change to stay within speed and slow slew rates
    if (rudder_delta > 0) {
        if (actual_rudder_value < NEUTRAL_RUDDER) {
            if (rudder_delta > slow_rate) rudder_delta = slow_rate;
        } else
            if (rudder_delta > speed_rate) rudder_delta = speed_rate;
    } else {
        if (actual_rudder_value > NEUTRAL_RUDDER) {
            if (rudder_delta < -slow_rate) rudder_delta = -slow_rate;
        } else
            if (rudder_delta < -speed_rate) rudder_delta = -speed_rate;
    }
    adjust_rudder_position(actual_rudder_value + rudder_delta);
}

uint16_t commanded_rudder_value = NEUTRAL_RUDDER; // 0-999 is starboard, 1001 to 2000 is port.  1000 is neutral.
// Sets global vars:
// * actual_rudder_value
// * commanded_rudder_value
// * brake_on
void stop_rudder_command()
{
    brake_on = 0;
    adjust_rudder_position(NEUTRAL_RUDDER); // NEUTRAL_RUDDER is stopped
    commanded_rudder_value = NEUTRAL_RUDDER;
}

// Sets global vars:
// * actual_rudder_value
// * commanded_rudder_value
// * brake_on
void stop_port()
{
    if (actual_rudder_value > NEUTRAL_RUDDER)
       stop_rudder_command();
}

// Sets global vars:
// * actual_rudder_value
// * commanded_rudder_value
// * brake_on
void stop_starboard()
{
    if (actual_rudder_value < NEUTRAL_RUDDER)
       stop_rudder_command();
}

void disengage()
{
    stop_rudder_command();
    flags &= ~ENGAGED;
    timeout = 30; // detach in about 62ms
    TCCR2A = 0;
    TCCR2B = 0;
    clutch_start_time = 0;
    digitalWrite(clutch_pin, LOW); // Release the clutch
}

void detach()
{
    TIMSK1 = 0;
    TCCR1A=0;
    TCCR1B=0;
    if (pwm_style) {
        while(digitalRead(pwm_output_pin)); // wait for end of pwm if pulse is high
        if (pwm_style == PWM_STYLE_VNH2SP30) {
            a_bottom_off;
            b_bottom_off;
            digitalWrite(enable_pin, LOW);
        }
    } else {
        timer1_state = 0;
        a_top_off;
        a_bottom_off;
        b_top_off;
        b_bottom_off;
    }
#if defined(__AVR_ATmega328pb__)
    if (pwm_style == PWM_STYLE_HBRIDGE_ATMEGA328PB)
        TIMSK4 = 0;
    else
#endif
        TIMSK2 = 0;

#ifdef BLINK
    static uint32_t led_blink;
    led_blink++;
    if (led_blink < 1500)
        digitalWrite(led_pin, HIGH); // status LED
    else
        digitalWrite(led_pin, LOW); // status LED
    if (led_blink > 20000)
        led_blink = 0;
#else
    digitalWrite(led_pin, LOW); // status LED
#endif
    
    timeout = 33; // avoid overflow
}

void engage()
{
    if (flags & ENGAGED)
        return; // already engaged

    if (pwm_style == PWM_STYLE_RC) {
        TCNT1 = 0x1fff;
        //Configure TIMER1
        TCCR1A=_BV(COM1A1)|_BV(WGM11);        //NON Inverted PWM
        TCCR1B=_BV(WGM13)|_BV(WGM12)|_BV(CS11); //PRESCALER=8 MODE 14(FAST PWM)
        ICR1=40000/DIV_CLOCK;  //fPWM=50Hz (Period = 20ms Standard).
        TIMSK1 = 0;
    } else if (pwm_style == PWM_STYLE_VNH2SP30) {
        TCNT1 = 0;
        TCCR1A=_BV(COM1A1)|_BV(WGM11);        //NON Inverted PWM
        TCCR1B=_BV(WGM13)|_BV(WGM12)|_BV(CS10); //PRESCALER=0 MODE 14(FAST PWM)

        // use 1khz safe at all speeds.   20khz is nice to avoid
        // audible sound, but you need to set minimum speed to 20-30%
        // or it will overheat the part at very low speeds.
        ICR1=16000/DIV_CLOCK;  //fPWM=1khz
        TIMSK1 = 0;

        digitalWrite(hbridge_a_bottom_pin, LOW);
        digitalWrite(hbridge_b_bottom_pin, LOW);
        digitalWrite(enable_pin, LOW);

        pinMode(hbridge_a_bottom_pin, OUTPUT);
        pinMode(hbridge_b_bottom_pin, OUTPUT);
        pinMode(enable_pin, OUTPUT);

        digitalWrite(enable_pin, HIGH);
    } else {
        //Configure TIMER1
        timer1_state = 0;
        TIMSK1 = 0;
        TCNT1 = 0;
        TCCR1A=_BV(WGM11);        //NON Inverted PWM
        TCCR1B=_BV(WGM13)|_BV(WGM12)|_BV(CS10); //PRESCALER=0 MODE 14(FAST PWM)
        ICR1=16000/DIV_CLOCK;  //fPWM=1khz

        a_top_off;
        a_bottom_off;
        b_top_off;
        b_bottom_off;

        pinMode(hbridge_a_bottom_pin, OUTPUT);
        pinMode(hbridge_b_bottom_pin, OUTPUT);
        pinMode(hbridge_a_top_pin, OUTPUT);
        pinMode(hbridge_b_top_pin, OUTPUT);
    }

    adjust_rudder_position(NEUTRAL_RUDDER);
    digitalWrite(clutch_pin, HIGH); // clutch
    clutch_start_time = 20;
    TCCR2A = 0;

    if (!digitalRead(clutch_sense_pwm_pin) && ratiometric_mode)
        TCCR2B = _BV(CS20); // divide 1 and pwm ~16khz;
    else
        TCCR2B = _BV(CS21); // divide 8 and 2khz or fast pwm 4khz if not ratiometric
    digitalWrite(led_pin, HIGH); // status LED
    flags |= ENGAGED;
}

// set hardware pwm to period of "(1500 + 1.5*value)/2" or "750 + .75*value" microseconds

enum {CURRENT, VOLTAGE, CONTROLLER_TEMP, MOTOR_TEMP, RUDDER, NUM_CHANNELS}; // adc_channel values
const uint8_t muxes[] = {
	_BV(MUX0), 
	0, 
	_BV(MUX1), 
	_BV(MUX0) | _BV(MUX1), 
	_BV(MUX2)
};

// adc_results_t is where the analog IO happens.
volatile struct adc_results_t {
    uint32_t total;
    uint16_t count;
} adc_results[NUM_CHANNELS][2];

// Analog register interface.
// This is where the adc IO happens.  It could be handled on an interrupt thread (USE_ADC_ISR is 1)
// or (as is the case in this code) it's manually called at various places in the code (service_adc).
// The operation of the adc_isr code varies depending on the value of the adc_channel. The adc_channel can be
// one of a number of values:
// * CURRENT
// * VOLTAGE
// * RUDDER
// * CONTROLLER_TEMP
// * MOTOR_TEMP
// (NUM_CHANNELS is a max value).
//
// take 4 channels, 4 samples of each using last sample,
// except for current, 50 samples, discarding first 3
// total 62 measurements, each measurement takes 13 cycles,
// channel change takes 12 cycles, total is 854 cycles,
// 16mhz / 128 / 854 = 146 samples/s, except for current,
// has 6862 samples/s
uint8_t adc_channel;
uint8_t adc_cycles_until_stable;
void adc_isr()
{
    uint16_t adcw = ADCW;
    if (++adc_cycles_until_stable <= 3) // Wait for channel values to stabilize.
        return;

    for (int i=0; i<2; i++) {
        if (adc_results[adc_channel][i].count < 4000) {
            adc_results[adc_channel][i].total += adcw;
            adc_results[adc_channel][i].count++;
        }
    }

    switch(adc_channel) {
    case CURRENT:
        if (adc_cycles_until_stable < 50) return;
        adc_channel = VOLTAGE;
        break;
    case VOLTAGE:
        if (adc_cycles_until_stable < 8) return;
        adc_channel = CONTROLLER_TEMP;
        break;
    case CONTROLLER_TEMP:
        adc_channel = MOTOR_TEMP;
        break;
    case MOTOR_TEMP:
        adc_channel = RUDDER;
        break;
    case RUDDER:
        if (rudder_sense && adc_cycles_until_stable < 16) return;
        adc_channel = CURRENT;
        break;
    default:
        adc_channel = CURRENT;
    }
    adc_cycles_until_stable = 0; // advance to next channel

    // Skip disabled channels.
#ifdef DISABLE_VOLTAGE_SENSE
    if (adc_channel == VOLTAGE) adc_channel = CONTROLLER_TEMP;
#endif
#ifdef DISABLE_TEMP_SENSE
    if (adc_channel == CONTROLLER_TEMP) adc_channel = RUDDER;
#endif
#ifdef DISABLE_RUDDER
    if (adc_channel == RUDDER) adc_channel = CURRENT;
#endif
    ADMUX = adcref | muxes[adc_channel]; // Request the next channel.
}

// Arduino Interrupt Handler
ISR(ADC_vect)
{
    sei();
    adc_isr();
    ADCSRA |= _BV(ADSC); // enable conversion
}

// Return the count for the requested channel.
// For disabled channels, return 0.
uint16_t CountADC(uint8_t adc_channel, uint8_t p)
{
    return adc_results[adc_channel][p].count;
}

// Return value of total and count from adc_results at [adc_channel][p]
// Reset total and count of adc_results back to 0.
// return value from 0-16368
uint16_t TakeADC(uint8_t adc_channel, uint8_t p)
{
    uint32_t t, c;
    cli();
    t = adc_results[adc_channel][p].total;
    c = adc_results[adc_channel][p].count;
    adc_results[adc_channel][p].total = 0;
    adc_results[adc_channel][p].count = 0;
    sei();
    return (c == 0)
        ? 0
        : (16 * t) / c;  // multiply by 16 to keep less significant bits
}

uint16_t TakeAmps(uint8_t p)
{
    uint32_t v = TakeADC(CURRENT, p);

    if (pwm_style == PWM_STYLE_VNH2SP30) // VNH2SP30
        return v * 9 / 34 / 16;
    
    if (low_current) {
    // current units of 10mA
    // 275 / 128 = 100.0/1024/.05*1.1   for 0.05 ohm shunt
    // 1375 / 128 = 100.0/1024/.01*1.1   for 0.01 ohm shunt
        if (shunt_resistance)
            v = v * 275 / 128 / 16;

        if (v > 16)
            v = v * 1375 / 128 / 16 + 16; // 550mA minimum
        else
            v = 0;
    } else { // high current
        if (v <= 16)
            v = 0;
        else  {
            if (shunt_resistance)
                //  .0005 ohm with 50x gain
                // 275/64 = 100.0/1024/.0005/50*1.1
                v = v * 275 / 64 / 16;
            else
                //  .0005 ohm with 200x gain (5v ref)
                // 625/128 = 100.0/1024/.0005/200*5
                v = v  * 525 / 128 / 16;
        }
    }
    return v;
}

uint16_t TakeVolts(uint8_t p)
{
    // voltage in 10mV increments 1.1ref, 560 and 10k resistors
    uint32_t v = TakeADC(VOLTAGE, p);

    if (ratiometric_mode)
        // 100.0/1024*115000/15000*5.0
        v = v * 1439 / 384 / 16;
    else if (voltage_mode == VOLTAGE_MODE_24V)
        // 14135 / 3584 = 100.0/1024*10280/280*1.1
        v = v * 14135 / 3584 / 16;
    else
        // 1815 / 896 = 100.0/1024*10560/560*1.1
        //    v = v * 1815 / 896 / 16;
        v = v * 1790 / 896 / 16; // hack closer to actual voltage

    return v;
}

uint16_t TakeTemp(uint8_t adc_channel, uint8_t p)
{
    uint32_t v = TakeADC(adc_channel, p), R;
    if (ratiometric_mode) {
        // thermistors are 10k resistor to 5v, and 10k NTC to GND with 5.0v ref
        // V = 5.0 * v / 1024
        // V = R / (R + 10k) * 5.0
        // x = 5.0 / 5.0 * v / 1024
        // R = 10k * x / (1 - x)
        // x = v / 1024
        // R = 10k * v / (1024*16 - v)

        R = 10000 * v / (16384 - v);  // resistance in ohms

        //  I accidentally put 100k resistors on board: R = 100000 * v / (16384 - v);  // resistance in ohms
    } else {
        // thermistors are 100k resistor to 5v, and 10k NTC to GND with 1.1v ref
        // V = 1.1 * v / 1024
        // V = R / (R + 100k) * 5.0
        // x = 1.1 / 5.0 * v / 1024
        // R = 100k * x / (1 - x)
        // R = 22000 * v / 1024 / (1 - 1.1 / 5.0 * v / 1024)

        R = 100061 * v / (74464 - v);  // resistance in ohms
    }
    // T0 = 298, B = 3905, R0 = 10000
    // T = 1 / (1 / T0 + 1/B * ln(R/R0))
    // T = 1.0 / (1.0 / 298.0 + 1/3905.0 * math.log(R/10000.0)) - 273.0

    // a reasonable approximation to avoid floating point math over our range:
    // within 2 degrees from 30C to 80C
    // T = 300000/(R+2600) + 2

    // temperature in hundreths of degrees
    return 30000000/(R+2600) + 200;
}

uint16_t TakeRudder(uint8_t p)
{
    // 16 bit value for rudder
    return TakeADC(RUDDER, p) * 4;
}

ISR(WDT_vect)
{
    wdt_reset();
    wdt_disable();
    if (!calculated_clock) {
        calculated_clock = 1; // use watchdog interrupt once at startup to compute the crystal's frequency
        return;
    }
    // normal watchdog event (program stuck)
    disengage();
    _delay_ms(50);
    detach();

    TCCR0B = 0; // apparently only needed on 16mhz boards
    asm volatile ("ijmp" ::"z" (0x0000)); // soft reset
}

ISR(TIMER1_OVF_vect) __attribute__((naked));
ISR(TIMER1_OVF_vect)
{
    asm volatile ("push r24"); // this register used to read timer1_state
    // bitwise and because compiler generates sbrs that does not affect flags and works in naked isr
    if (timer1_state & 1) {  // forward pwm
        asm volatile ("nop"); // balance 2 cycle delay of rjmp
        asm volatile ("nop"); // to get symmetric drive times
        asm volatile ("nop"); // waste 3 more cycles: lds
        asm volatile ("nop"); // (stupid compiler loads timer1_state into r24 every time)
        asm volatile ("nop");
        a_top_off;
        dead_time;
        a_bottom_on;
        asm volatile ("pop r24");  // no need to rjmp
        asm volatile ("reti");
    }

    if (timer1_state & 2) { // backward pwm
        b_top_off;
        dead_time;
        b_bottom_on;
        asm volatile ("pop r24");  // no need to rjmp
        asm volatile ("reti");
    }

    if (timer1_state & 4) { // forward steady (pulse to recharge gate cap)
        a_top_off;
        dead_time;
        a_bottom_on;
        charge_time;
        a_bottom_off;
        b_top_off;
        dead_time;
        a_top_on;
        b_bottom_on;
    } else if (timer1_state & 8) { // reverse steady
        b_top_off;
        dead_time;
        b_bottom_on;
        charge_time;
        b_bottom_off;
        a_top_off;
        dead_time;
        b_top_on;
        a_bottom_on;
    }
    
    asm volatile ("pop r24");
    asm volatile ("reti");
}

// use naked interrupts for maximum reaction
// this improves the upper range especially at
// 16khz with only 4mhz clock
ISR(TIMER1_COMPA_vect) __attribute__((naked));
ISR(TIMER1_COMPA_vect)
{
    a_bottom_off;
    b_top_off; // should already be off
    dead_time;
    a_top_on;
    b_bottom_on;
    asm volatile ("reti");
}

ISR(TIMER1_COMPB_vect) __attribute__((naked));
ISR(TIMER1_COMPB_vect)
{
    b_bottom_off;
    a_top_off; // should already be off
    dead_time;
    b_top_on;
    a_bottom_on;
    asm volatile ("reti");
}

#if USE_ADC_ISR
#define service_adc(X) // do nothing
#else
void service_adc() {
    if (ADCSRA & _BV(ADSC)) // data not ready
        return;

    adc_isr();
    ADCSRA |= _BV(ADSC); // start conversion
}
#endif
ISR(PCINT2_vect) {
}

// process_command
// A "command" packet consists of three bytes (stored in in_bytes):
// 0: The 8-bit command. see enum commands, above.
// 1 & 2: The value.  in_bytes[1] = least significant, in_bytes[2] is most significant.
void process_command()
{
    flags |= SYNC;
    uint16_t value = in_bytes[1] | in_bytes[2]<<8;
    switch(in_bytes[0]) {
    case REPROGRAM_CODE:
    {
        // jump to bootloader
        asm volatile ("ijmp" ::"z" (0x3c00));
        //goto *0x3c00;
    } break;
    case RESET_CODE:
        // reset overcurrent flag
        flags &= ~OVERCURRENT_FAULT;
        break;
    case COMMAND_CODE:
        timeout = 0;
        if (serialin < 12)
            serialin+=4; // output at input rate
        if (value > 2000);
            // unused range, invalid!!!  ignored
        else if (flags & (OVERTEMP_FAULT | OVERCURRENT_FAULT | BADVOLTAGE_FAULT));
            // no command because of overtemp or overcurrent or badvoltage
        else if ((flags & (PORT_PIN_FAULT | MAX_RUDDER_FAULT)) && value > NEUTRAL_RUDDER)
            stop_rudder_command(); // no port command if port fault
        else if ((flags & (STARBOARD_PIN_FAULT | MIN_RUDDER_FAULT)) && value < NEUTRAL_RUDDER)
            stop_rudder_command(); // no starboard command if starboard fault
        else {
            brake_on = use_brake;
            //brake_on = 1; //TESTING (remove this line!)
            commanded_rudder_value = value;
            engage();
        }
        break;
    case MAX_CURRENT_CODE: { // current in units of 10mA
        unsigned int max_max_current = low_current ? 2000 : 5000;
        if (value > max_max_current) // maximum is 20 or 50 amps
            value = max_max_current;
        max_current = value;
    } break;
    case MAX_CONTROLLER_TEMP_CODE:
        if (value > 10000) // maximum is 100C
            value = 10000;
        max_controller_temp = value;
        break;
    case MAX_MOTOR_TEMP_CODE:
        if (value > 10000) // maximum is 100C
            value = 10000;
        max_motor_temp = value;
        break;
    case RUDDER_MIN_CODE:
        rudder_min = value;
        break;
    case RUDDER_MAX_CODE:
        rudder_max = value;
        break;
    case DISENGAGE_CODE:
        if (serialin < 12)
            serialin+=4; // output at input rate
        disengage();
        break;
    case MAX_SLEW_CODE: {
        max_slew_speed = in_bytes[1];
        max_slew_slow = in_bytes[2];

        // if set at the end of range (up to 255)  no slew limit
        if (max_slew_speed > 250)
            max_slew_speed = 250;
        if (max_slew_slow > 250)
            max_slew_slow = 250;
        // must have some slew
        if (max_slew_speed < 1)
            max_slew_speed = 1;
        if (max_slew_slow < 1)
            max_slew_slow = 1;
    } break;
    case EEPROM_READ_CODE:
        if (eeprom_read_addr == eeprom_read_end) {
            eeprom_read_addr = in_bytes[1];
            eeprom_read_end = in_bytes[2];
        }        
    break;
    case EEPROM_WRITE_CODE:
        eeprom_update_8(in_bytes[1], in_bytes[2]);
        break;
    case CLUTCH_PWM_AND_BRAKE_CODE:
    {
        uint8_t pwm = in_bytes[1];
        if (pwm < 30)
            pwm = 30;
        else if (pwm > 250)
            pwm = 255;
        clutch_pwm = in_bytes[1];
        use_brake = in_bytes[2];
    } break;
    }
  service_adc();
}

void handle_timeouts() {
    // did timer2 pass MAX_TIMER_TICKS?
    // Timer2 ticks at 3906hz (4mhz), so this is ~50hz
    uint8_t ticks;
#if defined(__AVR_ATmega328pb__)
    if (pwm_style == PWM_STYLE_HBRIDGE_ATMEGA328PB)
        ticks = TCNT4;
    else
#endif        
        ticks = TCNT0;
    if (ticks > MAX_TIMER_TICKS) {
        static uint8_t timeout_d;
        // divide timeout for faster clocks, timeout counts at 50hz
        if (++timeout_d >= 4/DIV_CLOCK) {
            if (flags & ENGAGED) update_command(); // update speed changes to slew speed

            if (clutch_start_time) {
                if (--clutch_start_time == 0 && clutch_pwm < 250) {
                    OCR2A = clutch_pwm;
                    TCCR2A = _BV(WGM20) | _BV(COM2A1); // phase correct pwm
                }
	    }
            timeout_d = 0;
            timeout++;
            serial_data_timeout++;
        }
#if defined(__AVR_ATmega328pb__)
        if (pwm_style == PWM_STYLE_HBRIDGE_ATMEGA328PB)
            TCNT4 -= MAX_TIMER_TICKS;
        else
#endif
            TCNT0 -= MAX_TIMER_TICKS;
    }
    if (timeout == 30) disengage();
    if (timeout > 32)  detach(); // detach 62 ms later so electronic speed controller (ESC) gets stop
    if (serial_data_timeout > 250 && timeout>32) { // no serial data for 10 seconds, enter power down
        TCNT0 = 0;
        // while sleeping continuously reboots every 8 seconds with watchdog to ensure not stuck
        cli();
        WDTCSR = (1<<WDCE)|(1<<WDE);
        WDTCSR = (1<<WDIE) | (1<<WDP3) | (1<<WDP0);
        sei();
        PCICR |= _BV(PCIE2); // pin change interrupt
        PCMSK2 = _BV(PD0); // rx
        set_sleep_mode(SLEEP_MODE_PWR_DOWN);  // not working
        sleep_enable();
        sleep_cpu();
        cli();
        PCICR = 0;
        PCMSK2 = 0;
        wdt_reset();
        WDTCSR = (1<<WDCE)|(1<<WDE); // watchdog back to 0.25 seconds
        WDTCSR = (1<<WDIE) | (1<<WDP2);
        sei();
        serial_data_timeout -= 5;
    }
}



void loop()
{
    TIMSK0 = 0; // disable timer0 interrupt: millis is not used!
    wdt_reset(); // strobe watchdog
    service_adc();
    handle_timeouts();

    // Read all available serial input.
    while(Serial.available()) {
      uint8_t c = Serial.read();
      serial_data_timeout = 0;
      service_adc();
      if (sync_b < 3) {
      	  // Load 3 bytes at a time into in_bytes
          in_bytes[sync_b] = c;
          sync_b++;
      } else {
          if (c == crc8(in_bytes, 3)) {
              if (in_sync_count >= 2) { // if crc matches, we have a valid packet
                  process_command();

              } else {
                  in_sync_count++;
	          }
              sync_b = 0;
              flags &= ~INVALID;
          } else {
              // invalid packet
              flags &= ~SYNC;
              stop_rudder_command();
              in_sync_count = 0;
	      for (int i = 0; i < 2; i++) in_bytes[i] = in_bytes[i+1]; // Shift bytes to the left, append last byte.
              in_bytes[2] = c;
              flags |= INVALID;
          }
          break;
      }
    }

    // Test and set port/starboard fault pins
    if (!digitalRead(port_fault_pin)) {
        stop_port();
        flags |= PORT_PIN_FAULT;
    } else {
        flags &= ~PORT_PIN_FAULT;
    }

    if (!digitalRead(starboard_fault_pin)) {
        stop_starboard();
        flags |= STARBOARD_PIN_FAULT;
    } else {
        flags &= ~STARBOARD_PIN_FAULT;
    }
    service_adc();

    // Check OVERCURRENT_FAULT - 2000sps @ 8mhz
    const int react_count = 400/DIV_CLOCK;
    if (CountADC(CURRENT, 1) > react_count) {
        uint16_t amps = TakeAmps(1);
        if (amps >= max_current) {
            stop_rudder_command();
            faults |= OVERCURRENT_FAULT;
        } else
            faults &= ~OVERCURRENT_FAULT;
    }
    service_adc();

    // Check BADVOLTAGE_FAULT
    const int voltage_react_count = 400/DIV_CLOCK; // 200sps @ 8mhz 1s reaction
    if (CountADC(VOLTAGE, 1) > voltage_react_count) { // 1 second
        uint16_t volts = TakeVolts(1);
        if (volts >= 1800 && voltage_mode == VOLTAGE_MODE_12V && voltage_sense == LOW) {
            voltage_mode = VOLTAGE_MODE_24V; // switch from 12v mode to 24v mode
            digitalWrite(voltage_sense_pin, LOW); // changes voltage divider
            pinMode(voltage_sense_pin, OUTPUT);
            max_voltage = 3200; // increase max voltage to 32v
            _delay_ms(2);
            TakeVolts(0); // clear readings
            TakeVolts(1);
        } else
            /* voltage must be between 900 and max voltage, exclusive */
            if (volts <= 900 || volts >= max_voltage) {
                disengage(); // Sets ENGAGED flag to false
                flags |= BADVOLTAGE_FAULT;
        } else
            flags &= ~BADVOLTAGE_FAULT;
    }
    service_adc();

    flags |= faults;

    // test over temp
    const int temp_react_count = 100/DIV_CLOCK; // 1 second
    if (CountADC(CONTROLLER_TEMP, 1) > temp_react_count &&
       CountADC(MOTOR_TEMP, 1) > temp_react_count) {
        uint16_t controller_temp = TakeTemp(CONTROLLER_TEMP, 1);
        uint16_t motor_temp = TakeTemp(MOTOR_TEMP, 1);
        if (controller_temp >= max_controller_temp || motor_temp > max_motor_temp) {
            disengage();
            flags |= OVERTEMP_FAULT;
        } else
            flags &= ~OVERTEMP_FAULT;

        // 100C is max allowed temp, 117C is max measurable.
        // 110C indicates software fault
        if (controller_temp > 11000) {
            stop_rudder_command();
            TCCR0B = 0;
            asm volatile ("ijmp" ::"z" (0x0000)); // attempt soft reset
        }
    }
    service_adc();

    const int rudder_react_count = 100/DIV_CLOCK; // 400sps @ DIV_CLOCK=2 ~ approx 0.125 second reaction
    if (CountADC(RUDDER, 1) > rudder_react_count) {
        uint16_t v = TakeRudder(1);
        if (rudder_sense) {
            // if not positive, then rudder feedback has negative gain (reversed)
            uint8_t pos = rudder_min < rudder_max;
            
            if ((pos && v < rudder_min) || (!pos && v > rudder_min)) {
                stop_starboard();
                flags |= MIN_RUDDER_FAULT;
            } else
                flags &= ~MIN_RUDDER_FAULT;
            if ((pos && v > rudder_max) || (!pos && v < rudder_max)) {
                stop_port();
                flags |= MAX_RUDDER_FAULT;
            } else
                flags &= ~MAX_RUDDER_FAULT;
            if (v < 1024+1024 || v > 65472 - 1024)
                rudder_sense = 0;
        } else {
            if (v > 1024+1536 && v < 65472 - 1536)
                rudder_sense = 1;
            flags &= ~(MIN_RUDDER_FAULT | MAX_RUDDER_FAULT);
        }
    }
    service_adc();

    // Do the following for each of the 42 output command/value pairs:
    //
    // output 4 bytes, 1 byte at a time, as follows:
    // First time through "loop()", set crcbytes[0..2] to the output command and value. Write first byte (crcbytes[0])
    // Second and third time through "loop()" write crcbytes[1..2]
    // Fourth time through "loop()" output computed CRC code.
    if (byte_to_write_idx == 0) {
        // match output rate to input rate
        if (serialin < 4) return;

        uint16_t v;
        uint8_t code;

        //  flags C R V C R ct C R mt flags  C  R  V  C  R EE  C  R mct flags  C  R  V  C  R  EE  C  R rr flags  C  R  V  C  R EE  C  R cc  C  R vc
        //  0     1 2 3 4 5  6 7 8  9    10 11 12 13 14 15 16 17 18  19    20 21 22 23 24 25  26 27 28 29    30 31 32 33 34 35 36 37 38 39 40 41 42
        // Note that all but a few of the switch cases below have two exits: return, and break.
        // returns bypass the CRC output.  breaks allow them.
        switch(serial_command_to_output_idx++) {
        case 0: case 10: case 20: case 30:
            if (!low_current) flags |= CURRENT_RANGE;
            v = flags;
            flags &= ~REBOOTED;
            code = FLAGS_CODE;
            break;
        case 1: case 4: case 7: case 11: case 14: case 17: case 21: case 24: case 27: case 31: case 34: case 37: case 40:
            if (CountADC(CURRENT, 0) < 50) return;
            v = TakeAmps(0);
            code = CURRENT_CODE;
            serialin-=4; // fix current output rate to input rate
            break;
        case 2: case 5: case 8: case 12: case 15: case 18: case 22: case 25: case 28: case 32: case 35: case 38: case 41:
            if (CountADC(RUDDER, 0) < 10 || (!rudder_sense && serial_command_to_output_idx > 3)) return;
            if (rudder_sense == 0)
                v = 65535; // indicate invalid rudder measurement
            else
                v = TakeRudder(0);
            code = RUDDER_SENSE_CODE;
            break;
        case 3: case 13: case 23: case 33:
            if (CountADC(VOLTAGE, 0) < 2) return;
            v = TakeVolts(0);
            code = VOLTAGE_CODE;
            break;
        case 6:
            if (CountADC(CONTROLLER_TEMP, 0) == 0) return;
            v = TakeTemp(CONTROLLER_TEMP, 0);
            code = CONTROLLER_TEMP_CODE;
            break;
        case 9:
            if (CountADC(MOTOR_TEMP, 0) == 0)  return;
            v = TakeTemp(MOTOR_TEMP, 0);
            if (v > 1200) code = MOTOR_TEMP_CODE; // below 12C means no sensor connected, or too cold to care
            break;
        case 16: case 26: case 36: /* eeprom reads */
            if (eeprom_read_addr == eeprom_read_end) return;
            uint8_t value;
            if (eeprom_read_8(eeprom_read_addr, value)) {
                v = value << 8 | eeprom_read_addr;
                eeprom_read_addr++;
                code = EEPROM_VALUE_CODE;
                serial_command_to_output_idx--; // fast eeprom read
            } else {
                eeprom_read_addr++; // skip for now
            }
            break;
        default:
            return;
        }
        // Set the serial output command.
        crcbytes[0] = code;
        crcbytes[1] = v;
        crcbytes[2] = v>>8;
    }
    // Cause output command to be written one byte per loop iteration.
    if (byte_to_write_idx < 3) {
        Serial.write(crcbytes[byte_to_write_idx]);
        ++byte_to_write_idx;
    } else {
        Serial.write(crc8(crcbytes, 3));
        byte_to_write_idx = 0;
    }
}

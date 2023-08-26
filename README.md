# Sailboat Autopilot

## Overview

This is a marine autopilot, with a web interface.

## Details

### PiCore Help

See PiCore_Hints_and_Tips.txt

### Software
Uses python3 for the brain and the web interface.  Run the web server using the `run_webserver.sh` script -- that starts everything.
The motor controller 

The autopilot brain is contained entirely within the Python code which runs on the RPi0.  The Python code writes to
and reads from the motor controller using Serial IO and ascii strings.  It is basically telling the controller:
* Whether to turn the rudder
* How fast to turn the rudder
* How far to turn the rudder

The motor controller can talk back to the brain with some status, the most important of which is the rudder position.

Operations on the motor controller are:

* Set the motor clutch state (enabled or disabled)
* Set the motor speed 
* Set the motor direction 
* Set rudder limits
* Get status including rudder position

### Sample Arduino Output

```
i=1000 # Status interval ms
p=0000 # Rudder position. 0 (max left) <= 512 (center) <= 1023 (max right)
x=0 # Limit fault direction. 0 = none, 1 = left, 2 = right.
d=0 # Direction 0 (none), 1 (left), 2 (right)
c=0 # Clutch status. 0 (off), 1 (on)
s=000 # Motor speed 0 (stationary) <= speed <= 255 (max)
l=0000 # Left rudder limit
r=1023 # Right rudder limit.
m=message string
```

### Hardware
The hardware for this project consists of: 

* 12v power supply
* "Brain" components
  * Raspberry Pi Zero W (RPi0W)
  * MPU-9250 position and motion sensor
* Motor controller components:
  * Arduino Nano (mega328p) motor controller 
  * IBT-2 PWM-based 30A reversible motor driver
* Actuator
  * Existing autopilot hardware consisting of hydraulic ram and motor. 
    The motor is intended to be a variable-speed, reversible hydraulic motor driving a linear ram. The motor contains a clutch/solenoid which opens or closes a valve on the hydraulic ram.  When open, the helmsman can turn the wheel freely, and the autopilot won't steer.  When closed, the helm is controlled by the hydraulic ram, and the wheel cannot be manually turned. Speed is controlled with PWM from the Arduino through the PWM-capable IBT-2.


## Connections to the IBT-2 board:
```
IBT-2     Arduino
pin desc  pin - MODE
--------  ---------------------------------------
  1 RPWM  10  - PWM Green - ANALOG
  2 LPWM   9  - PWM Blue  - ANALOG
  3 R_EN   3  - +5v Yellow - DIGITAL -- R_EN and L_EN can be combined and connected to a +5v source.
  4 L_EN   2  - +5v Lt. Brown - DIGITAL -- R_EN and L_EN can be combined and connected to a +5v source.
  5 R_IS   -  - NOT CONNECTED
  6 L_IS   -  - NOT CONNECTED
  7 VCC    -  - +5v Red +5v
  8 GND    -  - GND
IBT-2 pin 1 (RPWM) to Arduino pin 5(PWM)
IBT-2 pin 2 (LPWM) to Arduino pin 6(PWM)
IBT-2 pins 3 (R_EN), 4 (L_EN), 7 (VCC) to +5V (e.g. Arduino 5v pin)
IBT-2 pin 8 (GND) to Arduino GND
IBT-2 pins 5 (R_IS) and 6 (L_IS) not connected
```

## Calibration of the IMU
To calibrate the IMU (get bias values), run mpu9250-calibration.py

## Author
```
Adrian Vrouwenvelder
2022

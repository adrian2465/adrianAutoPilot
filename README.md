# Sailboat Autopilot

## Overview

This is a from-scratch autopilot, based on:

* 12v power supply
* Raspberry Pi Zero "brain" (RPi0)
* MPU-9250 position and motion sensor
* Arduino Nano (mega328p) motor controller 
* IBT-2 PWM-based 30A reversible motor driver

The motor is intended to be a reversible hydraulic motor driving a linear ram. The motor contains a clutch/solenoid
which opens or closes a valve on the hydraulic ram.  When open, the helmsman can turn the wheel freely, and the 
autopilot won't steer.  When closed, the helm is controlled by the hydraulic ram, and the wheel cannot be manually
turned.

The autopilot logic is contained entirely within the Python code which runs on the RPi0.  The Python code writes to
and reads from the motor controller using Serial IO and semi-readable ascii strings.
The Arduino motor controller is intended to be pretty dumb, for simplicity.  It is designed as an "object' and as such 
supports "getter" and "setter" methods on the controller.

* Set the motor clutch state (enabled or disabled)
* Set the motor speed 
* Set the motor direction 
* Set rudder limits
* Get status including rudder position


## Connections to the IBT-2 board:
======================================================================
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

# MYPYPILOT

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
* Set the motor speed (0-9)
* Set the motor direction (left, right, stopped) 
* Set rudder limits
* Get rudder position
* Get rudder stop switches (These may be hard-wired as digital pin stops in on the arduino. There's nothing to configure here, and
  going past the stops would be destructive and pointless).


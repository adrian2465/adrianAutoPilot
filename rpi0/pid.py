import sys
import time
import math
from anglemath import calculate_angle_difference
from boat import Boat
from config import Config as BoatConfig

# P = Proportional
# I = Integral -- Sum of errors
# D = Derivative -- Slope of correction
# Output = P + I + D  = Actuator control command
# Gains (configurable): p_gain, i_gain, d_gain.  Can be supplied as parameters to main below, for CLI testing.
#
# This controller takes PV and SP as degrees (0-360).  
# The error is the smallest angle between those.
# The rudder control that's returned is a value between -1 <= output <= 1, with 0 being no action, -1 being move left, 
# and 1 being move rudder right.
#
# HINTS:
# - If the controller overshoots and/or oscillates, try increating the I gain, or decrease ALL the gains (P, I, and D gains)
# - If there's too much overshoot, try increasing D gain, or decreasing P gain
# - If the response is too dampened, try increasing the P gain.
# - Ramps up too quickly, then slows on approaching target and delaying the target arrival, try increasing I gain.
#
# RULE OF THUMB TRIAL-AND-ERROR TUNING:
# - Set I and D gains to zero. Increase P gain until output starts to oscillate. - This is the "Critical Gain"
#   Goal: Increase P to make the system correct faster, but do not destabilize the system.
# - Increase the I term to stop the oscillations.  Increasing I decreases steady-state error, but increases overshoot.
# - Increase D to account for overshoot.
#
# ZIEGLER NICHOLS METHOD FOR TUNING
# - Find Critical Gain (P gain) where oscillation starts
# - Pc is the period of oscillation
# - Kc is the critical gain value
# - i_gain = 0.5*Pc
# - d_gain = Pc/8

class PID:
  
    def __init__(self, boat_config):
        self.boat_config = boat_config
        self.err = 0 # error (e.g. smallest angle between actual heading and desired heading)
        self.prev_err = 0 # Previous error
        self.dt = 100 # Time in MS to wait between samples/commands
        self.output = 0 # Output signal to send to correction actuator (e.g. the rudder) 0 = no action. -1 and 1 are maxes
        self.p_gain = boat_config.get_P_gain() # Tunable Proportional gain
        print(f"p_gain is {self.p_gain}")
        self.i_gain = boat_config.get_I_gain() # Tunable Integral gain
        self.d_gain = boat_config.get_D_gain() # Tunable Derivative gain
        self.p_val = 0 # P
        self.i_val = 0 # I
        self.d_val = 0 # D
        self.process_value = 0
   
    def set_course(self, course): # Desired value
        self.course = course
        self.err = 360

    def get_output(self): # Get actuator control value
        return self.output

    def compute_rudder_deflection(self, process_value): # Process using PID algorithm
        self.err = calculate_angle_difference(self.course, process_value) 
        self.p_val = self.p_gain * self.err
        self.i_val = self.i_val + self.err * self.i_gain * self.dt
        self.d_val = self.d_gain * (self.prev_err - self.err) / self.dt
        self.prev_err = self.err
        output = -self.p_val + self.i_val + self.d_val
        # Normalize output to -1 <= output <= 1. Output will be 
        if output > 1: 
            print(f"WARNING: Correcting deflection from {output} to 1 - Adjust gains if this is common")
            print(f"p_val={self.p_val:6.2f} err={self.err:6.2f} i_val={self.i_val:6.2f} d_val={self.d_val:6.2f}")
            output = 1 # Don't go past max deflection
        if output < -1:
            print(f"WARNING: Correcting deflection from {output} to -1 - Adjust gains if this is common ")
            print(f"p_val={self.p_val:6.2f} err={self.err:6.2f} i_val={self.i_val:6.2f} d_val={self.d_val:6.2f}")
            output = -1 # Don't go past max deflction
        self.output = output
        return output

    def wait(self):
        time.sleep(self.dt / 1000) # Convert dt (in ms) to seconds.

if __name__ == "__main__":
    args = sys.argv[1:]
    boat_config = BoatConfig("config.yaml" if len(args) == 0 else args[0])
    print(f"boat_config.p_gain is {boat_config.get_P_gain()}")
    print(f"INFO Using configuration {boat_config.filename}")
    boat = Boat(boat_config)

    course = 100.0
    initial_heading = 200.0
    print(f"boat_config.p_gain is {boat_config.get_P_gain()}")
    pid = PID(boat_config)
    print(f"time, process_value, heading, err, output")
    start_time = time.time()

    pid.set_course(course) # Desired heading
    boat.sensor.heading = initial_heading # For testing - normally, the sensor provides the heading asynchronously
    while abs(pid.err) > 1:
        boat.set_rudder_angle(pid.compute_rudder_deflection(boat.sensor.get_heading()))
        boat.tick() 
        print(f"DEBUG time={time.time()-start_time:6.0f}, course={pid.course:6.2f}, heading={boat.sensor.heading:6.2f}, err={pid.err:6.2f}, deflection={pid.output:6.4f}")
        pid.wait()
    print(f"INFO  Correction from {initial_heading:6.2f} to {course:6.2f} took {time.time()-start_time:6.0f} seconds.")

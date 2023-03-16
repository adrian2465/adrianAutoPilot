from anglemath import calculate_angle_difference
# import time
from island_time import time # Make things simulate faster

# Author: Adrian Vrouwenvelder
#
# P = Proportional
# I = Integral -- Sum of errors
# D = Derivative -- Slope of correction
# Output = P + I + D  = Actuator control command
# Gains (configurable): p_gain, i_gain, d_gain.  Can be supplied as parameters to main below, for CLI testing.
#
# This controller takes PV and SP as degrees (0-360).  
# The error is the smallest angle between those.
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
  
    def __init__(self, p_gain, i_gain, d_gain, sampling_interval_ms):
        self.p_gain = p_gain # Tunable Proportional gain
        self.i_gain = i_gain # Tunable Integral gain
        self.d_gain = d_gain # Tunable Derivative gain
        self.dt = sampling_interval_ms # Sample interval, in ms

        self.err = 0 # error (e.g. smallest angle between actual heading and desired heading)
        self.prev_err = 0 # Previous error
        self.p_val = 0 # P
        self.i_val = 0 # I
        self.d_val = 0 # D
   
    def calc_error(self, process_value):
        self.err = calculate_angle_difference(self.target_value, process_value) 
    
    def set_target_value(self, target_value): # Desired value
        self.target_value = target_value
        self.calc_error(0)

    def compute_output(self, process_value): # Process using PID algorithm
        self.calc_error(process_value)
        self.p_val = self.p_gain * self.err
        self.i_val = self.err * self.i_gain * self.dt + self.i_val
        self.d_val = self.d_gain * (self.prev_err - self.err) / self.dt
        self.prev_err = self.err
        return self.p_val + self.i_val + self.d_val

    def wait(self):
        time.sleep(self.dt / 1000)  # Convert dt (in ms) to seconds.

def test_pv(target, p_gain, i_gain, d_gain, pv):
    pid = PID(p_gain, i_gain, d_gain, 10)
    pid.set_target_value(target)
    output = pid.compute_output(pv)
    print(f"Output for Gains = (p_gain={pid.p_gain:6.2} i_gain={pid.i_gain:6.2} d_gain={pid.d_gain:6.2}) Target={pid.target_value:6.2f} to PV={pv:6.2f}. Error is {pid.err:10.8f}. Correction is {output:6.2f}")

# For testing only
if __name__ == "__main__":
    test_pv(100, 2.0, 0.0, 0.0, 1)
    test_pv(100, 2.0, 0.0, 0.0, 100)
    test_pv(100, 2.0, 0.0, 0.0, 150)

    test_pv(110, 1.5, 0.01, 0.01, 9)
    test_pv(110, 1.5, 0.01, 0.01, 110)
    test_pv(110, 1.5, 0.01, 0.01, 149)

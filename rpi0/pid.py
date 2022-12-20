import sys
import time
import math

# P = Proportional
# I = Integral -- Sum of errors
# D = Derivative -- Slope of correction
# Output = P + I + D  = Actuator control command
# Gains (configurable): p_gain, i_gain, d_gain.  Can be supplied as parameters to main below, for CLI testing.
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
  
    def __init__(self, p_gain, i_gain, d_gain):
        self.err = 0 # error (e.g. diff between actual heading and desired heading)
        self.prev_err = 0 # Previous error
        self.dt = 100 # Time in MS to wait between samples/commands
        self.output = 0 # Output signal to send to correction actuator (e.g. the rudder)
        self.p_gain = p_gain # Proportional gain
        self.i_gain = i_gain # Integral gain
        self.d_gain = d_gain # Derivative gain
        self.p_val = 0 # P
        self.i_val = 0 # I
        self.d_val = 0 # D
   
    def set_point(self, set_point): # Desired value
        self.set_point = set_point

    def get_output(self): # Get actuator control value
        return self.output

    def process_input(self, process_value):
        self.err = self.set_point - process_value
        self.p_val = self.p_gain * self.err
        self.i_val = self.i_val + self.err * self.i_gain * self.dt
        self.d_val = self.d_gain * (self.prev_err - self.err) / self.dt
        self.prev_err = self.err
        self.output = self.p_val + self.i_val + self.d_val
        return self.output

    def wait(self):
        time.sleep(self.dt / 1000) # Convert dt (in ms) to seconds.

if __name__ == "__main__":
    args = sys.argv[1:]
    iteration = 0
    pid = PID(float(args[0]),float(args[1]),float(args[2]))
    print("iteration, set, pv, p, i, d, err, output")
    pid.set_point(360) # Desired heading
    pv = 200 # Actual heading
    while(True):
        iteration = iteration + 1
        pid.process_input(pv)
        print(f"{iteration},{pid.set_point},{pv},{pid.p_val},{pid.i_val},{pid.d_val},{pid.err},{pid.output}")
        if (math.fabs(pid.err) < 2): break
        pv = pv + (pid.output * .20)


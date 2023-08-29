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
from anglemath import calculate_angle_difference
from time import time as real_time
from file_logger import logger, DEBUG

log = logger(dest=None)
log.set_level(DEBUG)


class PID:

    def __init__(self, cfg, time_fn=real_time):
        self._target_value = None
        self._gains = cfg.pid["gains"]["default"]
        self._prev_timestamp = 0
        self._time_fn = time_fn  # Supply island time to speed up testing
        self._prev_err = 0  # Previous error
        self._val = [0] * 3
        self._err = None

    @property
    def p_gain(self):
        return self._gains["P"]

    @property
    def i_gain(self):
        return self._gains["I"]

    @property
    def d_gain(self):
        return self._gains["D"]

    def p_val(self):
        return self._val[0]

    def set_p_val(self, v):
        self._val[0] = v

    def i_val(self):
        return self._val[1]

    def set_i_val(self, v):
        self._val[1] = v

    def d_val(self):
        return self._val[2]

    def set_d_val(self, v):
        self._val[2] = v

    def err(self):
        return self._err

    def set_err(self, v):
        self._err = v

    def set_target_value(self, target_value):  # Desired value
        log.debug(f"New target value is {target_value}")
        self._target_value = target_value
        self._err = None

    def compute_commanded_rudder(self, target_course: float, heading: float):  # Process using PID algorithm
        dt = self._time_fn() - self._prev_timestamp
        self._prev_timestamp = self._time_fn()
        self.set_err(calculate_angle_difference(target_course, heading))
        self.set_p_val(self.p_gain * self.err())
        self.set_i_val(self.i_val() + self.err() * self.i_gain * dt)
        self.set_d_val(self.d_gain * (self._prev_err - self.err()) / dt)
        self._prev_err = self.err()
        rc = -(self.p_val() + self.i_val() + self.d_val()) / 180
        commanded_rudder = 1 if rc > 1 else -1 if rc < -1 else rc  # Return desired correction.
        log.debug(f"hdg={heading} - tgt={target_course} => rdr={commanded_rudder}")
        return commanded_rudder

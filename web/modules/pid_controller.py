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

log = logger(dest=None, who="pid_controller")

class PID:

    def __init__(self, cfg, time_fn=real_time):
        gains = cfg.pid["gains"]["default"]
        if "log_level" in cfg.pid: log.set_level(int(cfg.pid["log_level"]))
        self._time_fn = time_fn  # Supply island time to speed up testing
        self._p_gain = gains["P"]
        self._i_gain = gains["I"]
        self._d_gain = gains["D"]
        self._p_val = 0
        self._i_val = 0
        self._d_val = 0
        self._prev_err = 0
        self._err = 0
        self._prev_timestamp = self._time_fn()

    def reset(self):
        self._p_val = 0
        self._i_val = 0
        self._d_val = 0
        self._prev_err = 0
        self._err = 0
        self._prev_timestamp = self._time_fn()

    def get_gains_as_csv(self):
        return f"{self._p_gain:5.3f},{self._i_gain:5.3f},{self._d_gain:5.3f}"

    def compute_commanded_rudder(self, target_course: float, heading: float):
        """Calculate updated commanded rudder angle using PID controller"""
        dt = self._time_fn() - self._prev_timestamp
        self._prev_timestamp = self._time_fn()
        self._err = calculate_angle_difference(target_course, heading)
        self._p_val = self._p_gain * self._err
        self._i_val = self._i_val + self._err * self._i_gain * dt
        self._d_val = self._d_gain * (self._prev_err - self._err) / dt
        rc = -(self._p_val + self._i_val + self._d_val) / 180
        commanded_rudder = 1 if rc > 1 else -1 if rc < -1 else rc  # Return desired correction.
        log.debug(f"hdg={heading} - tgt={target_course} => rdr={commanded_rudder}")
        self._prev_err = self._err
        return commanded_rudder

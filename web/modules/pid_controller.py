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
from boat import rudder_as_string
from config import Config


class PID:

    def __init__(self, config, time_fn=real_time):
        self._gains = config.pid["gains"]["default"]
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

    @property
    def p_val(self):
        return self._val[0]

    @p_val.setter
    def p_val(self, v):
        self._val[0] = v

    @property
    def i_val(self):
        return self._val[1]

    @i_val.setter
    def i_val(self, v):
        self._val[1] = v

    @property
    def d_val(self):
        return self._val[2]

    @d_val.setter
    def d_val(self, v):
        self._val[2] = v

    @property
    def err(self):
        return self._err

    @err.setter
    def err(self, v):
        self._err = v

    def set_target_value(self, target_value):  # Desired value
        log.debug(f"New target value is {target_value}")
        self._target_value = target_value
        self._err = None

    def output(self, process_value):  # Process using PID algorithm
        dt = self._time_fn() - self._prev_timestamp
        self._prev_timestamp = self._time_fn()
        self.err = calculate_angle_difference(self._target_value, process_value)
        self.p_val = self.p_gain * self.err
        self.i_val += self.err * self.i_gain * dt
        self.d_val = self.d_gain * (self._prev_err - self.err) / dt
        self._prev_err = self.err
        rc = -(self.p_val + self.i_val + self.d_val) / 180
        return 1 if rc > 1 else -1 if rc < -1 else rc  # Return desired correction.



# For testing
if __name__ == "__main__":
    from island_time import time as island_time
    from test_boat import BoatImpl
    from vectormath import moving_average_scalar
    from file_logger import logger, INFO, DEBUG

    log = logger(dest=None)
    log.set_level(DEBUG)
    test_time = island_time()

    def test_controller(boat, pid):
        log.debug(f"Starting run for pid.p={pid.p_gain:4.2f} pid.i={pid.i_gain:4.2f} pid.d={pid.d_gain:4.2f})")
        start_time = test_time.time()
        diff_avg = abs(calculate_angle_difference(boat.get_target_course(), boat.get_heading()))
        interval = 0.5  # seconds between samples
        j = 1000
        log.debug("TIME, COURSE, HEADING, RUDDER, RUDDER_STRING")
        log.debug(f"{0:5.2f}, {boat.get_target_course():6.2f}, {boat.get_heading():6.2f}, {boat.get_rudder():4.2f}, {rudder_as_string(boat.get_rudder())} ")
        while not (boat.is_on_course() and abs(boat.get_rudder()) <= 0.01):
            boat.set_commanded_rudder(pid.output(boat.get_heading()))
            # The following simulates what happens in the next time frame.
            test_time.sleep(interval)  # Simulation
            # Boat Simulation code. Actual rudder and boat turn rates would be determined by sensor.
            boat.update(interval)
            diff_avg = moving_average_scalar(diff_avg, abs(calculate_angle_difference(boat.get_target_course(), boat.get_heading())), 4)
            log.debug(f"{test_time.time() - start_time:5.2f}, {boat.get_target_course():6.2f}, {boat.get_heading():6.2f}, {boat.get_rudder():4.2f}, {rudder_as_string(boat.get_rudder())} ")
            j -= 1
            if j <= 0:
                break
            # if test_time.time() - start_time > 120:  # Break free if not there in 100 seconds
            #     log.debug("NOTE! Course did not settle in 2 minutes!!")
            #     break
        return test_time.time() - start_time

    config = Config("../../configuration/config.yaml")
    boat = BoatImpl(config)
    boat.set_heading(0)
    boat.set_target_course(100)
    boat.set_rudder(0)

    pid = PID(config, time_fn=test_time.time)
    pid.set_target_value(boat.get_target_course())
    log.debug(f"Testing controller. Starting at {boat.get_heading()}, going to {boat.get_target_course()}")
    t = test_controller(boat, pid)

    time_limit = 16.5
    if t > time_limit:
        raise Exception(f"Failed time test. Boat correction time {t} exceeded {time_limit} seconds")
    log.info(f"Course correction finished in {t} seconds. ")

from anglemath import calculate_angle_difference
from time import time as real_time

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

    def __init__(self, gain, time_fn=real_time):
        self._p_gain = gain[0]  # Tunable Proportional gain
        self._i_gain = gain[1]  # Tunable Integral gain
        self._d_gain = gain[2]  # Tunable Derivative gain
        self._prev_timestamp = 0
        self._time_fn = time_fn  # Supply island time to speed up testing
        self._prev_err = 0  # Previous error
        self._p_val = 0  # P
        self._i_val = 0  # I
        self._d_val = 0  # D
        self._err = None

    @property
    def p_gain(self):
        return self._p_gain

    @property
    def i_gain(self):
        return self._i_gain

    @property
    def d_gain(self):
        return self._d_gain

    @property
    def err(self):
        return self._err

    def set_target_value(self, target_value):  # Desired value
        self.target_value = target_value
        self._err = None

    def output(self, process_value):  # Process using PID algorithm
        dt = self._time_fn() - self._prev_timestamp
        self._prev_timestamp = self._time_fn()
        self._err = calculate_angle_difference(self.target_value, process_value)
        self._p_val = self.p_gain * self._err
        self._i_val += self._err * self.i_gain * dt
        self._d_val = self.d_gain * (self._prev_err - self._err) / dt
        self._prev_err = self._err
        rc = -(self._p_val + self._i_val + self._d_val) / 180
        return 1 if rc > 1 else -1 if rc < -1 else rc  # Return desired correction.



# For testing
if __name__ == "__main__":
    from island_time import time as island_time
    from testboat import BoatImpl
    from vectormath import moving_average_scalar
    from file_logger import logger, INFO, DEBUG
    boat = BoatImpl()
    log = logger(dest=None)
    log.set_level(INFO)
    test_time = island_time()

    def test_hard_over_time():
        global boat
        boat.heading = 1
        boat.course = 100
        start_time = test_time.time()
        interval = 0.5
        while boat.rudder < 1:
            boat.commanded_rudder = 1
            boat.update(interval)
            test_time.sleep(interval)
        duration = test_time.time() - start_time
        if duration <= 0.1:
            raise Exception(f"Rudder hard-over took {duration} s which is implausibly fast.")
        if duration > boat.hard_over_time:
            raise Exception(f"Rudder hard-over took {duration} s and should have completed within {boat.hard_over_time} s")
        log.info(f"Hardover completed in {duration} s")


    def test_controller(heading, course, gain):
        global boat
        boat.heading = heading
        boat.course = course
        pid = PID(gain, time_fn=test_time.time)
        pid.set_target_value(boat.course)
        log.debug(f"Starting run for H={boat.heading:5.2f} C={boat.course:6.2f} p={pid.p_gain:4.2f} i={pid.i_gain:4.2f} d={pid.d_gain:4.2f})")
        start_time = test_time.time()
        diff_avg = abs(calculate_angle_difference(boat.course, boat.heading))
        interval = 0.5  # seconds between samples
        j = 1000
        while not (boat.is_on_course and boat.rudder < 0.01):
            boat.commanded_rudder = pid.output(boat.heading)
            # The following simulates what happens in the next time frame.
            test_time.sleep(interval)  # Simulation
            # Boat Simulation code. Actual rudder and boat turn rates would be determined by sensor.
            boat.update(interval)
            diff_avg = moving_average_scalar(diff_avg, abs(calculate_angle_difference(boat.course, boat.heading)), 4)
            log.debug(f"T={test_time.time() - start_time} H={boat.heading:6.2f} {boat.rudder_as_string(boat.rudder)} ")
            j -= 1
            if j <= 0: break;
            # if test_time.time() - start_time > 120:  # Break free if not there in 100 seconds
            #     log.debug("NOTE! Course did not settle in 2 minutes!!")
            #     break
        return test_time.time() - start_time


    test_hard_over_time()

    best_pid = None
    best_t = None
    best_p = 0
    best_i = 0
    best_d = 0
    log.info("Looking for best p")
    p = 0
    while p <= 15:
        t = test_controller(1, 100, [p, best_i, best_d])
        if best_t is None or t < best_t:
            best_p, best_t = p, t
        p += 0.01
    log.info(f"Best p is {best_p}. Looking for i...")
    i = 0
    best_t = None
    while i <= 2:
        t = test_controller(1, 100, [best_p, i, best_d])
        if best_t is None or t < best_t:
            best_i, best_t = i, t
        i += 0.001
    log.info(f"Best i is {best_i}. Looking for d...")
    d = 0
    best_t = None
    while d <= .01:
        t = test_controller(1, 100, [best_p, best_i, d])
        if best_t is None or t < best_t:
            best_d, best_t = d, t
        d += 0.00001
    best_pid = [best_p, best_i, best_d]
    log.info(f"Best result for H=1, C=100 = {best_pid} in {best_t} s")
    log.set_level(DEBUG)
    t = test_controller(1, 100, best_pid)
    log.info(f"Finished in {t} seconds. ")

# Adrian Vrouwenvelder
# August 2023
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
# - If the controller overshoots and/or oscillates, try increating the I gain, or decrease ALL
#   the gains (P, I, and D gains)
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
import time
from modules.common.angle_math import calculate_acute_angle, normalize_angle, is_on_course
from modules.common.config import Config


class PID:
    P_idx = 0
    I_idx = 1
    D_idx = 2

    def __init__(self, gains='calm'):
        self._cfg = Config.getConfig()
        self._gains = self._cfg['pid_gains'][gains]
        self._prev_err = 0
        self._err_sum = 0
        self._prev_timestamp = time.time()

    def compute(self, course: float, heading: float):
        """Calculate updated commanded rudder angle using SIMPLE PID controller."""
        now = time.time()
        d_time = now - self._prev_timestamp
        error = calculate_acute_angle(heading, course)
        self._err_sum += error * d_time
        d_err = (error - self._prev_err) / d_time if d_time > 0 else 0.0
        output = self._gains[PID.P_idx] * error + \
                 self._gains[PID.I_idx] * self._err_sum + \
                 self._gains[PID.D_idx] * d_err
        output = max(-1, output) if output < 0 else min(1, output)
        self._prev_err = error
        self._prev_timestamp = now
        return output


if __name__ == "__main__":
    import sys

    Config.init()
    cfg = Config.getConfig()
    if len(sys.argv) != 4:
        print(f"Supply initial heading, course, rudder as arguments")
        exit(1)
    heading, course, rudder = [float(sys.argv[i]) for i in range(1, len(sys.argv))]
    hard_over_time_ms = cfg['rudder_hard_over_time_ms']
    rudder_turn_rate_ups = 1000 / hard_over_time_ms  # ups = unit per second. 1 unit is centered-to-hardover.
    boat_turn_rate_dps = cfg['boat_max_turn_rate_dps']
    rudder_position_tolerance = cfg['rudder_position_tolerance']
    course_tolerance_deg = cfg['course_tolerance_deg']
    pid = PID()
    interval_s = 0.25
    previous_time = time()
    max_iterations = 1000
    elapsed_s = 0
    time_between_iterations = 0.5
    data = []
    while not is_on_course(course, heading, course_tolerance_deg) and max_iterations > 0:
        max_iterations -= 1
        now = time()
        delta_t = now - previous_time
        previous_time = now
        desired_rudder = pid.compute(course, heading)
        if (desired_rudder - rudder) > rudder_position_tolerance:
            rudder = min(1.0, rudder + rudder_turn_rate_ups * delta_t)
        elif (rudder - desired_rudder) > rudder_position_tolerance:
            rudder = max(-1.0, rudder - rudder_turn_rate_ups * delta_t)
        heading = normalize_angle(heading + boat_turn_rate_dps * rudder * delta_t)
        print(f"Desired Rudder: {desired_rudder}, Actual Rudder: {rudder}, Heading: {heading}")
        time.sleep(time_between_iterations)
        elapsed_s += time_between_iterations
    if max_iterations == 0:
        print("Did not converge")
    else:
        print(f"On course with tolerance of {course_tolerance_deg} deg in {elapsed_s} seconds")

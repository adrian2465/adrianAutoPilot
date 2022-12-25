import sys
import logging
import math
from anglemath import calculate_angle_difference
from boat import Boat
from config import Config as BoatConfig
# import time
from island_time import time # Make things simulate faster

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

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s [%(filename)s] -  %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

class PID:
  
    def __init__(self, p_gain, i_gain, d_gain):
        self.err = 0 # error (e.g. smallest angle between actual heading and desired heading)
        self.prev_err = 0 # Previous error
        self.dt = 1000 # Sample rate, in ms
        self.output = 0 # Output signal from PID algorithm
        self.p_gain = p_gain # Tunable Proportional gain
        self.i_gain = i_gain # Tunable Integral gain
        self.d_gain = d_gain # Tunable Derivative gain
        self.p_val = 0 # P
        self.i_val = 0 # I
        self.d_val = 0 # D
        self.process_value = 0
   
    def set_target_value(self, target_value): # Desired value
        self.target_value = target_value
        self.err = 360

    def get_output(self): # Get actuator control value
        return self.output

    def compute_output(self, process_value): # Process using PID algorithm
        self.err = -calculate_angle_difference(self.target_value, process_value) 
        self.p_val = self.p_gain * self.err
        self.i_val = self.i_val + self.err * self.i_gain * self.dt
        self.d_val = self.d_gain * (self.prev_err - self.err) / self.dt
        self.prev_err = self.err
        output = self.p_val + self.i_val + self.d_val
        self.output = output
        return output

    def wait(self):
        time.sleep(self.dt / 1000)  # Convert dt (in ms) to seconds.


if __name__ == "__main__":
    import csv
    from datetime import datetime
    produce_csv = True
    args = sys.argv[1:]
    current_time = datetime.now()
    boat_config = BoatConfig("config.yaml" if len(args) == 0 else args[0])
    filename = f"{current_time.strftime('pid_%Y%m%d-%H%M%S.csv')}"
    with open(filename, 'w', newline='') as csvfile:
        logging.debug(f"Using configuration {boat_config.filename}")
        logging.debug(f"Gains: P = {boat_config.get_P_gain()} I = {boat_config.get_I_gain()} D = {boat_config.get_D_gain()}")
        boat = Boat(boat_config)
        target_value = 100.0
        initial_heading = 200.0
        logging.debug(f"target = {target_value} heading = {initial_heading}")
        pid = PID(boat_config.get_P_gain(), boat_config.get_I_gain(), boat_config.get_D_gain())
        start_time = time.time()
        if produce_csv: 
            csvwriter = csv.writer(csvfile, delimiter=',')
            csvwriter.writerow([f"{target_value:6.2f}",f"{initial_heading:6.2f}",f"{boat_config.get_P_gain():6.4f}",f"{boat_config.get_I_gain():6.4f}",f"{boat_config.get_D_gain():6.4f}",f"{boat.max_rudder_deflection_deg:6.2f}",f"{boat.rudder_speed_dps:6.2f}",f"{boat.max_boat_turn_rate_dps:6.2f}"])
            csvwriter.writerow(["time","pv","err","output","rudder","heading","course","p_gain","i_gain","d_gain","max_rudder_deflection","rudder_speed","max_boat_turn_rate"])
        pid.set_target_value(target_value) # Desired heading
        boat.sensor.heading = initial_heading # For testing - normally, the sensor provides the heading asynchronously
        logging.debug(f"info,timestamp, target_value, heading, err, pid_output, rudder_angle")
        while abs(pid.err) > 1:
            boat.request_rudder_angle(pid.compute_output(process_value=boat.sensor.get_heading()))
            timestamp = time.time() - start_time
            if produce_csv: 
                csvwriter.writerow([f"{timestamp:6.2f}",f"{boat.sensor.heading:6.2f}",f"{pid.err:6.2f}",f"{pid.output:6.4f}",f"{boat.current_rudder_deflection_deg:6.2f}",f"{target_value:6.2f}",f"{initial_heading:6.2f}",f"{boat_config.get_P_gain():6.4f}",f"{boat_config.get_I_gain():6.4f}",f"{boat_config.get_D_gain():6.4f}",f"{boat.max_rudder_deflection_deg:6.2f}",f"{boat.rudder_speed_dps:6.2f}",f"{boat.max_boat_turn_rate_dps:6.2f}"])
            boat.tick() 
            logging.debug(f"time={timestamp:6.2f}, target={pid.target_value:6.2f}, pv={boat.sensor.heading:6.2f}, err={pid.err:6.2f}, output={pid.output:6.4f}, rudder={boat.current_rudder_deflection_deg:6.2f}")
            pid.wait()
        logging.debug(f"Correction from {initial_heading:6.2f} to {target_value:6.2f} took {time.time()-start_time:6.0f} seconds.")
        if produce_csv: logging.info(f"Output of run in file {csvfile}")

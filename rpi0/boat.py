# Author: Adrian Vrouwenvelder
from island_time import time # Make things simulate faster
import logging
import sys
from config import Config as BoatConfig
from anglemath import calculate_angle_difference, normalize_angle
from sensor import Sensor

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(filename)s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)
# logger.setLevel(level=logging.DEBUG)


class Boat:
    def __init__(self, boat_config):
        self.max_boat_turn_rate_dps = float(boat_config.get_boat_turn_rate_dps()) # Angular velocity of boat with rudder hard over. TODO: Consider speed, point of sail
        self.rudder_speed_dps = float(boat_config.get_rudder_speed_dps()) # Speed at which actuator moves rudder rudder. Determine empirically.
        self.max_rudder_deflection_deg = float(boat_config.get_max_rudder_deflection_deg()) # Maximum rudder deflection. Determine empirically.
        self.commanded_rudder_deflection_deg = float(0.0) # Desired rudder deflection.
        self.current_rudder_deflection_deg = float(0.0) # Current rudder deflection
        self.sampling_interval_ms = float(boat_config.get_sampling_interval_ms()) # Time between loop iterations, in ms
        self.sensor = Sensor() # Simulate sensor module (gives heading, speed, etc)
        self.Max_Balanced_Rudder_Angle = float(15.0) # Rudder deflection required to go straight TODO: Consider heel angle, speed, point of sail.

        # In a real world
        # The following are used only for simulating real conditions, to test with.
        # They would ordinarily come from the boat sensor unit
        now_s = time.time()
        self.prev_heading_adjustment_time_s = now_s
        self.prev_rudder_adjustment_time_s = now_s

    # Request positive to turn to right. Negative to turn to left.
    # Rudder action does not happen immediately because the rudder needs time to move into position.
    def request_rudder_angle(self, commanded_rudder_deflection_deg):
        if commanded_rudder_deflection_deg > self.max_rudder_deflection_deg: 
            logger.debug(f" NOTE: corrected {commanded_rudder_deflection_deg:6.0f} to {self.max_rudder_deflection_deg:4.0f}")
            commanded_rudder_deflection_deg = self.max_rudder_deflection_deg
        elif commanded_rudder_deflection_deg < -self.max_rudder_deflection_deg: 
            logger.debug(f" NOTE: corrected {commanded_rudder_deflection_deg:6.0f} to {-self.max_rudder_deflection_deg:4.0f}")
            commanded_rudder_deflection_deg = -self.max_rudder_deflection_deg
        self.commanded_rudder_deflection_deg = commanded_rudder_deflection_deg
         
    # In a real world, heading "adjustment" would be unnecessary - heading is a result of rudder adjustment, and is obtained from the sensor.
    # Also, rudder angle would be determined empirically from the sensor.
    def tick(self):
        now_s = time.time()
        dt_s = now_s - self.prev_rudder_adjustment_time_s
        self.prev_rudder_adjustment_time_s = now_s
        rudder_deflection_diff_deg = -calculate_angle_difference(self.commanded_rudder_deflection_deg, self.current_rudder_deflection_deg)
        if abs(rudder_deflection_diff_deg) > .1: # if equal to 0, the rudder is already at the requested angle - no need to move
            # Start the rudder moving in the right direction.
            direction_of_movement = 1 if rudder_deflection_diff_deg >= 0 else -1
            rudder_adjustment_deg = direction_of_movement * self.rudder_speed_dps * dt_s # Max the rudder could have moved in dt_s
            self.current_rudder_deflection_deg = self.current_rudder_deflection_deg + rudder_adjustment_deg
            if self.current_rudder_deflection_deg > self.max_rudder_deflection_deg: self.current_rudder_deflection_deg = self.max_rudder_deflection_deg
            if self.current_rudder_deflection_deg < -self.max_rudder_deflection_deg: self.current_rudder_deflection_deg = -self.max_rudder_deflection_deg

        dt_s = now_s - self.prev_heading_adjustment_time_s
        self.prev_heading_adjustment_time_s = now_s
        # Keep turning the boat at whatever rate the current rudder angle prescribes
        # Note that rudder_percent and therefore boat_turn_rate_dps are signed due to self.current_rudder_deflection_deg being signed.
        rudder_percent = self.current_rudder_deflection_deg / self.max_rudder_deflection_deg 
        boat_turn_rate_dps = rudder_percent * self.max_boat_turn_rate_dps 
        # Update the heading sensor artificially - since this is just a simulator, it won't update itself.
        self.sensor.heading = normalize_angle(self.sensor.heading + boat_turn_rate_dps * dt_s)
        logger.debug(f"TICK: t={time.time():4.1f}, commanded rudder = {self.commanded_rudder_deflection_deg:6.0f} current rudder={self.current_rudder_deflection_deg:4.0f}, heading={self.sensor.heading:4.0f}")

# For testing only
# The following demonstrates rudder action's effect on boat heading
if __name__ == "__main__":
    args = sys.argv[1:]
    boat = Boat(BoatConfig("config.yaml" if len(args) == 0 else args[0]))

    boat.sensor.heading = 0
    logger.debug("***** Simulating course change right from 0 to 90 with rudder angle of 45")
    boat.request_rudder_angle(45)
    iterations = 0
    now_s = time.time()
    # Allow boat to turn until heading is 90 or time is exceeded.
    while boat.sensor.heading < 90 and (time.time() - now_s < 60):
        boat.tick()
        time.sleep(1)

    logger.debug(f"***** t={time.time()} - Simulating course change left to 80 with rudder angle of -5")
    boat.request_rudder_angle(-5)
    now_s = time.time()
    while boat.sensor.heading > 80 and (time.time() - now_s < 60):
        boat.tick()
        time.sleep(1)

# Author: Adrian Vrouwenvelder
from island_time import time # Make things simulate faster
import logging
import sys
from config import Config as BoatConfig
from anglemath import calculate_angle_difference
from sensor import Sensor

def send_to_arduino(x):
    if (x > 45 or x < -45): raise Exception("YOU BROKE THE RUDDER WITH ANGLE {x}")
    direction = " to the right" if x > 0 else " to the left"
    logging.debug(f"ARDUINO SIMULATOR: setting rudder deflection = {x:6.2f} {direction}")

class Boat:
   
    def __init__(self, boat_config):
        self.max_boat_turn_rate_dps = float(boat_config.get_boat_turn_rate_dps()) # Angular velocity of boat with rudder hard over. Determine empirically.
        self.rudder_speed_dps = float(boat_config.get_rudder_speed_dps()) # Speed at which actuator moves rudder rudder. Determine empirically.
        self.max_rudder_deflection_deg = float(boat_config.get_max_rudder_deflection_deg()) # Maximum rudder angle. Determine empirically.
        self.sampling_interval_ms = float(boat_config.get_sampling_interval_ms()) # Maximum rudder angle. Determine empirically.
        self.commanded_rudder_deflection_deg = float(0.0)
        self.current_rudder_deflection_deg = float(0.0)
        self.sensor = Sensor()
        self.Max_Balanced_Rudder_Angle = float(15.0) # Given weather helm, rudder deflection required to go straight

        # In a real world
        # The following are used only for simulating real conditions, to test with.
        # They would ordinarily come from the boat sensor unit
        now_s = time.time()
        self.prev_heading_adjustment_time_s = now_s
        self.prev_rudder_adjustment_time_s = now_s

    # Request positive to turn to right. Negative to turn to left.
    def request_rudder_angle(self, commanded_rudder_deflection_deg):
        self.commanded_rudder_deflection_deg = commanded_rudder_deflection_deg
        if commanded_rudder_deflection_deg > self.max_rudder_deflection_deg: 
            logging.debug(f"request_rudder_angle({commanded_rudder_deflection_deg:3.0f}) NOTE: corrected to {self.max_rudder_deflection_deg:3.0f}")
            commanded_rudder_deflection_deg = self.max_rudder_deflection_deg
        elif commanded_rudder_deflection_deg < -self.max_rudder_deflection_deg: 
            logging.debug(f"request_rudder_angle({commanded_rudder_deflection_deg:3.0f}) NOTE: corrected to {-self.max_rudder_deflection_deg:3.0f}")
            commanded_rudder_deflection_deg = -self.max_rudder_deflection_deg
        else: 
            logging.debug(f"request_rudder_angle({commanded_rudder_deflection_deg:3.0f} deg)")
        send_to_arduino(commanded_rudder_deflection_deg)
        
    # In a real world, heading "adjustment" would be unnecessary - heading is a result of rudder adjustment, and is obtained from the sensor.
    # Also, rudder angle would be determined empirically from the sensor.
    def tick(self):
        logging.debug("tick")
        now_s = time.time()
        dt_s = now_s - self.prev_rudder_adjustment_time_s
        self.prev_rudder_adjustment_time_s = now_s
        if abs(calculate_angle_difference(self.current_rudder_deflection_deg, self.commanded_rudder_deflection_deg)) > .1: # if equal to 0, the rudder is already at the requested angle - no need to move
            # Start the rudder moving in the right direction.
            direction_of_command = 1 if self.commanded_rudder_deflection_deg >= 0 else -1
            commanded_rudder_adjustment_deg = direction_of_command * self.rudder_speed_dps * dt_s # Max the rudder could have moved in the given time.
            self.current_rudder_deflection_deg = self.current_rudder_deflection_deg + commanded_rudder_adjustment_deg 
            if self.current_rudder_deflection_deg > self.max_rudder_deflection_deg: self.current_rudder_deflection_deg = self.max_rudder_deflection_deg
            if self.current_rudder_deflection_deg < -self.max_rudder_deflection_deg: self.current_rudder_deflection_deg = -self.max_rudder_deflection_deg

        dt_s = now_s - self.prev_heading_adjustment_time_s
        self.prev_heading_adjustment_time_s = now_s
        rudder_percent = self.current_rudder_deflection_deg / self.max_rudder_deflection_deg # rudder_percent is signed due to self.current_rudder_deflection_deg
        boat_turn_rate_dps = rudder_percent * self.max_boat_turn_rate_dps # Boat turn rate already is signed due to rudder percent
        # logging.debug(f"Current rudder deflection is {self.current_rudder_deflection_deg:6.2f}; Heading before is {self.sensor.heading}. Adjusting heading from {self.sensor.heading:6.2f} by {boat_turn_rate_dps * dt_s:6.2f}")
        self.sensor.heading =  self.sensor.heading + boat_turn_rate_dps * dt_s

# For testing only
# The following demonstrates rudder action's effect on boat heading
if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(filename)s %(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S')

    logger = logging.getLogger(__name__)
    # logger.setLevel(level=logging.DEBUG)

    args = sys.argv[1:]
    boat_config = BoatConfig("config.yaml" if len(args) == 0 else args[0])
    boat = Boat(boat_config)

    logger.debug("***** Simulating course change from 0 to 90 with rudder angle of 45")
    boat.request_rudder_angle(45)
    iterations = 0
    now_s = time.time()
    while boat.sensor.heading < 90 and (time.time() - now_s < 20):
        boat.tick()
        logger.debug(f"rudder_angle={boat.current_rudder_deflection_deg:6.2f}, heading={boat.sensor.heading:6.2f}")
        time.sleep(1)

    boat.sensor.heading = 90
    logger.debug("***** Simulating course change from 90 to 80 with rudder angle of 5")
    boat.request_rudder_angle(-5)
    now_s = time.time()
    while boat.sensor.heading > 80 and (time.time() - now_s < 20):
        boat.tick()
        logger.debug(f"rudder_angle={boat.current_rudder_deflection_deg:6.2f}, heading={boat.sensor.heading:6.2f}")
        time.sleep(1)

# Author: Adrian Vrouwenvelder
import time
import sys
from config import Config as BoatConfig
from anglemath import calculate_angle_difference
from sensor import Sensor


def send_to_arduino(x):
    print(f"Sent to arduino: rudder deflection = {x}")

class Boat:
   
    def __init__(self, boat_config):
        self.max_boat_turn_rate_dps = float(boat_config.get_boat_turn_rate_dps()) # Angular velocity of boat with rudder hard over. Determine empirically.
        self.rudder_speed_dps = float(boat_config.get_rudder_speed_dps()) # Speed at which actuator moves rudder rudder. Determine empirically.
        self.max_rudder_deflection_deg = float(boat_config.get_max_rudder_deflection_deg()) # Maximum rudder angle. Determine empirically.
        self.commanded_rudder_deflection_deg = float(0.0)
        self.current_rudder_deflection_deg = float(0.0)
        self.sensor = Sensor()

        # In a real world
        # The following are used only for simulating real conditions, to test with.
        # They would ordinarily come from the boat sensor unit
        now_s = time.time()
        self.prev_heading_adjustment_time_s = now_s
        self.prev_rudder_adjustment_time_s = now_s

    def set_rudder_angle(self, commanded_rudder_deflection_deg):
        if commanded_rudder_deflection_deg > self.max_rudder_deflection_deg: 
            print(f"WARNING: Commanded rudder value of {commanded_rudder_deflection_deg:3.0f} deg exceeds max of {self.max_rudder_deflection_deg:3.0f}")
            commanded_rudder_deflection_deg = self.max_rudder_deflection_deg
        elif commanded_rudder_deflection_deg < -self.max_rudder_deflection_deg: 
            print(f"WARNING: Commanded rudder value of {commanded_rudder_deflection_deg:3.0f} deg exceeds max of {-self.max_rudder_deflection_deg:3.0f}")
            commanded_rudder_deflection_deg = -self.max_rudder_deflection_deg
        self.commanded_rudder_deflection_deg = commanded_rudder_deflection_deg
        send_to_arduino(self.commanded_rudder_deflection_deg)
        
    # In a real world, heading "adjustment" would be unnecessary - heading is a result of rudder adjustment, and is obtained from the sensor.
    # Also, rudder angle would be determined empirically from the sensor.
    def tick(self):
        now_s = time.time()
        angle_difference = calculate_angle_difference(self.current_rudder_deflection_deg, self.commanded_rudder_deflection_deg)
        if abs(angle_difference) > .1: # if equal to 0, the rudder is already at the requested angle - no need to move
            # Start the rudder moving in the right direction.
            dt_s = now_s - self.prev_rudder_adjustment_time_s
            self.prev_rudder_adjustment_time_s = now_s
            delta_deflection_deg = self.rudder_speed_dps * dt_s # Max the rudder could have moved in the given time.
            delta_deflection_deg = -delta_deflection_deg if angle_difference < 0 else delta_deflection_deg
            self.current_rudder_deflection_deg = self.current_rudder_deflection_deg + delta_deflection_deg 
            if abs(self.current_rudder_deflection_deg) > abs(self.commanded_rudder_deflection_deg): self.current_rudder_deflection_deg = self.commanded_rudder_deflection_deg
            if self.current_rudder_deflection_deg > self.max_rudder_deflection_deg: self.current_rudder_deflection_deg = self.max_rudder_deflection_deg
            if self.current_rudder_deflection_deg < -self.max_rudder_deflection_deg: self.current_rudder_deflection_deg = -self.max_rudder_deflection_deg

        dt_s = now_s - self.prev_heading_adjustment_time_s
        self.prev_heading_adjustment_time_s = now_s
        rudder_percent = self.current_rudder_deflection_deg / self.max_rudder_deflection_deg
        boat_turn_rate_dps = rudder_percent * self.max_boat_turn_rate_dps
        self.sensor.heading = boat_turn_rate_dps * dt_s + self.sensor.heading

# The following demonstrates rudder action's effect on boat heading
if __name__ == "__main__":
    args = sys.argv[1:]
    boat_config = BoatConfig("config.yaml" if len(args) == 0 else args[0])
    boat = Boat(boat_config)

    print("***** Simulating course change from 0 to 90 with rudder angle of 45")
    boat.set_rudder_angle(45)
    while boat.sensor.heading < 90:
        boat.tick()
        print(f"rudder_angle={boat.current_rudder_deflection_deg:6.2f}, heading={boat.sensor.heading:6.2f}")
        time.sleep(1)

    boat.sensor.heading = 90
    print("***** Simulating course change from 90 to 80 with rudder angle of 5")
    boat.set_rudder_angle(-5)
    while boat.sensor.heading > 80:
        boat.tick()
        print(f"rudder_angle={boat.current_rudder_deflection_deg:6.2f}, heading={boat.sensor.heading:6.2f}")
        time.sleep(1)
    # while True:
        # LEFT OFF HERE: The PID controller is what should be updating the rudder angle.
        # however, the sensor update should be "simulated" as above, in tick.  
        # Maybe read from a file where we can asynchronously inject "disturbance"


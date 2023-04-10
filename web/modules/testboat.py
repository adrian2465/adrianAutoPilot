from config import Config
from anglemath import normalize_angle
from boat import Boat

class BoatImpl(Boat):

    def __init__(self):
        super().__init__()
        cfg = Config("../../configuration/config.yaml").boat
        self._rudder_hardover_time_s = cfg['rudder_hardover_time_s']  #  From Center -- for simulations.
        self._max_boat_turn_rate_dps = cfg['boat_turn_rate_dps']  #  From Center -- for simulations.

    @property
    def hard_over_time(self):
        return self._rudder_hardover_time_s

# Override
    def update(self, elapsed_time):  # For Simulation. Normally, get this from sensor.
        max_rudder_adjustment = elapsed_time / self._rudder_hardover_time_s
        rudder_direction = 1 if self.commanded_rudder > self.rudder else -1
        requested_rudder_adjustment = abs(self.commanded_rudder - self.rudder)
        rudder_adjustment = rudder_direction * (\
            requested_rudder_adjustment if requested_rudder_adjustment <= max_rudder_adjustment \
                else max_rudder_adjustment)
        self.rudder += rudder_adjustment
        self.rudder = 1 if self.rudder > 1 else -1 if self.rudder < -1 else self.rudder
        self.heading = normalize_angle(self.heading + self._max_boat_turn_rate_dps * elapsed_time * self.rudder)
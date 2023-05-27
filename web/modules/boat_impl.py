from config import Config
from anglemath import normalize_angle
from boat import Boat
from sensor import Sensor
from arduinoInterface import ArduinoInterface

class BoatImpl(Boat):

    def __init__(self, sensor: Sensor, arduino: ArduinoInterface):
        super().__init__()
        # cfg = Config("../../configuration/config.yaml").boat
        self._sensor: Sensor = sensor
        self._arduino: ArduinoInterface = arduino

    @property
    def heading(self):
        """Boat's current heading."""
        return self._sensor.heading()

    @property
    def heel(self):
        """Angle of heel in degrees. 0 = level"""
        return self._sensor.heel_angle_deg()

    @property
    def rudder(self):
        """Returns normalized rudder (-1 for full port, 1 for full starboard, 0 for centered)"""
        return self._arduino.get_rudder()

    def update(self, elapsed_time):  # For Simulation. Normally, get this from sensor.
        max_rudder_adjustment = elapsed_time / self._rudder_hardover_time_s
        rudder_direction = 1 if self.commanded_rudder > self._rudder else -1
        requested_rudder_adjustment = abs(self.commanded_rudder - self._rudder)
        rudder_adjustment = rudder_direction * (\
            requested_rudder_adjustment if requested_rudder_adjustment <= max_rudder_adjustment \
                else max_rudder_adjustment)
        self._rudder += rudder_adjustment
        self._rudder = 1 if self._rudder > 1 else -1 if self._rudder < -1 else self._rudder
        self._heading = normalize_angle(self._heading + self._max_boat_turn_rate_dps * elapsed_time * self._rudder)
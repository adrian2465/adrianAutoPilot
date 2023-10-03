from modules.common.anglemath import normalize_angle
from modules.interfaces.boat_interface import BoatInterface
from modules.common.config import Config
from modules.common.file_logger import Logger
import time

_log = Logger(config_path="boat", dest=None, who="boat_simulator")


class BoatImpl(BoatInterface):

    def __init__(self, cfg):
        super().__init__(cfg)

        self._heading = 0
        self._heel = 0
        self._rudder = 0
        self._prev_time = None

    def heading(self):
        """Boat's current heading."""
        return self._heading

    def heel(self):
        """Angle of heel in degrees. 0 = level"""
        return self._heel

    def rudder(self):
        """Returns normalized rudder (-1 for full port, 1 for full starboard, 0 for centered)"""
        return self._rudder

    def set_heading(self, heading):
        if heading == self._heading:
            return
        _log.debug(f"New heading set on simulated boat={heading}")
        self._heading = heading

    def set_heel(self, heel):
        if heel == self._heel:
            return
        _log.debug(f"New heel set on simulated boat={heel}")
        self._heel = heel

    def set_rudder(self, rudder):
        if rudder == self._rudder:
            return
        _log.debug(f"New rudder set on simulated boat={rudder}")
        self._rudder = 1 if (rudder > 1) else -1 if (rudder < -1) else rudder

    def update_heading(self, elapsed_time_s):
        """Update heading based on the rudder angle and elapsed time.  motor_direction is -1 for port, 1 for starboard."""
        _log.debug(f"update_heading(t={elapsed_time_s}")
        self.set_heading(normalize_angle(self.heading() + self.max_boat_turn_rate_dps() * elapsed_time_s * self.rudder()))

    def update_rudder(self, elapsed_time_s, direction):
        """Update rudder angle based on elapsed time and direction of autopilot motor"""
        _log.debug(f"update_rudder(t={elapsed_time_s}, dir={direction}")
        self.set_rudder(self.rudder() + direction * elapsed_time_s / self.hard_over_time_s())

    def update_rudder_and_heading(self, motor_direction):  # For Simulation. Normally, get this from sensor.
        """Update rudder and heading based on what the rudder is doing.  motor_direction is -1 for left, 1 for right."""
        elapsed_time = 0 if self._prev_time is None else (time.time() - self._prev_time)
        self._prev_time = time.time()
        _log.debug(f"update_rudder_and_heading(t={elapsed_time}, md={motor_direction})")
        new_rudder = self.rudder() + motor_direction * (elapsed_time / self.hard_over_time_s())
        self.set_rudder(new_rudder)
        self.set_heading(
            normalize_angle(self.heading() + self.max_boat_turn_rate_dps() * elapsed_time * self.rudder()))

# For testing


if __name__ == "__main__":
    from modules.simulator.time_simulator import time as island_time
    from boat_simulator import BoatImpl
    test_time = island_time()

    def test_hard_over_time(boat):
        start_time = test_time.time()
        prev_time = start_time
        interval = 0.5
        boat.set_rudder(0)
        motor_direction = 1
        duration = 0
        while boat.rudder() < 1:
            test_time.sleep(interval)
            duration = test_time.time() - prev_time
            prev_time = test_time.time()
            boat.update_rudder(duration, motor_direction)

        elapsed_time = test_time.time() - start_time
        if elapsed_time < 4:
            raise Exception(f"Rudder hard-over took {duration} s which is implausibly fast.")
        if elapsed_time > boat.hard_over_time_s():
            raise Exception(f"Rudder hard-over took {duration} s and "
                            f"should have completed within {boat.hard_over_time_s()} s")
        _log.info(f"Hardover completed in {duration} s")

    def test_boat_keeps_turning(boat):
        start_time = test_time.time()
        prev_time = start_time
        interval = 0.5
        boat.set_heading(0)
        boat.set_rudder(1)  # Hard to starboard
        old_heading = boat.heading()
        for i in range(0, 20):
            test_time.sleep(interval)
            duration = test_time.time() - prev_time
            prev_time = test_time.time()
            boat.update_heading(duration)

        if boat.heading() - old_heading != boat.max_boat_turn_rate_dps() * interval * 20:
            raise Exception(f"Heading not expected. old={old_heading}, new={boat.heading()}, "
                            f"expected={old_heading + boat.max_boat_turn_rate_dps() * 20 * interval} "
                            f"turnrate={boat.max_boat_turn_rate_dps()}")
        if boat.rudder() != 1:
            raise Exception("Rudder moved without motor action")
        _log.info(f"Keeps-turning test completed ")


    cfg = Config("configuration/config.yaml")
    test_boat = BoatImpl(cfg)
    _log.debug(f"Testing hardover time. Starting at rudder={test_boat.rudder()}")
    test_hard_over_time(test_boat)
    test_boat_keeps_turning(test_boat)

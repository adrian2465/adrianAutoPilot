from anglemath import normalize_angle
from boat_interface import BoatInterface
from config import Config
from file_logger import logger, DEBUG

log = logger(dest=None)
log.set_level(DEBUG)


class BoatImpl(BoatInterface):

    def __init__(self, config):
        super().__init__(config)
        self._heading = 0
        self._heel = 0
        self._rudder = 0

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
        log.debug(f"New heading set on simulated boat={heading}")
        self._heading = heading

    def set_heel(self, heel):
        if heel == self._heel:
            return
        log.debug(f"New heel set on simulated boat={heel}")
        self._heel = heel

    def set_rudder(self, rudder):
        if rudder == self._rudder:
            return
        log.debug(f"New rudder set on simulated boat={rudder}")
        self._rudder = rudder

    def update_rudder_and_heading(self, elapsed_time, motor_direction):  # For Simulation. Normally, get this from sensor.
        """Update rudder and heading based on what the rudder is doing.  motor_direction is -1 for left, 1 for right."""
        new_rudder = self.rudder() + motor_direction * (elapsed_time / self.hard_over_time_s())
        self.set_rudder(1 if new_rudder > 1 else -1 if new_rudder < -1 else new_rudder)
        self.set_heading(
            normalize_angle(self.heading() + self.max_boat_turn_rate_dps() * elapsed_time * self.rudder()))

# For testing


if __name__ == "__main__":
    from island_time import time as island_time
    from boat_simulator import BoatImpl
    test_time = island_time()

    def test_hard_over_time(boat):
        start_time = test_time.time()
        interval = 0.5
        motor_direction = 1
        while boat.rudder() < 1:
            boat.update_rudder_and_heading(interval, motor_direction)
            test_time.sleep(interval)
        duration = test_time.time() - start_time
        if duration <= 0.1:
            raise Exception(f"Rudder hard-over took {duration} s which is implausibly fast.")
        if duration > boat.hard_over_time_s():
            raise Exception(f"Rudder hard-over took {duration} s and "
                            f"should have completed within {boat.hard_over_time_s()} s")
        log.info(f"Hardover completed in {duration} s")

    def test_boat_keeps_turning(boat):
        interval = 0.5
        motor_direction = 0
        old_heading = boat.heading()
        for i in range(0, 20):
            boat.update_rudder_and_heading(interval, motor_direction)
            test_time.sleep(interval)
        new_heading = boat.heading()
        if new_heading - old_heading != boat.max_boat_turn_rate_dps() * interval * 20:
            raise Exception(f"Heading not expected. old={old_heading}, new={new_heading}, "
                            f"expected={old_heading + boat.max_boat_turn_rate_dps() * 20 * interval} "
                            f"turnrate={boat.max_boat_turn_rate_dps()}")
        if boat.rudder() != 1:
            raise Exception("Rudder moved without motor action")
        log.info(f"Keeps-turning test completed ")


    test_boat = BoatImpl(Config("../../configuration/config.yaml"))
    log.debug(f"Testing hardover time. Starting at rudder={test_boat.rudder()}")
    test_hard_over_time(test_boat)
    test_boat_keeps_turning(test_boat)

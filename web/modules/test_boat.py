from anglemath import normalize_angle
from boat import Boat
from config import Config

class BoatImpl(Boat):

    def __init__(self, config):
        super().__init__(config)
        self._heading = 0
        self._heel = 0
        self._rudder = 0

    def set_heading(self, heading):
        self._heading = heading

    def set_heel(self, heel):
        self._heel = heel

    def set_rudder(self, rudder):
        self._rudder = rudder

    def update(self, elapsed_time):  # For Simulation. Normally, get this from sensor.
        max_rudder_adjustment = elapsed_time / self.get_hard_over_time_s()
        rudder_direction = 1 if self.get_commanded_rudder() > self.get_rudder() else -1
        requested_rudder_adjustment = abs(self.get_commanded_rudder() - self.get_rudder())
        rudder_adjustment = rudder_direction * ( \
            requested_rudder_adjustment if requested_rudder_adjustment <= max_rudder_adjustment \
                else max_rudder_adjustment)
        self.set_rudder(self.get_rudder() + rudder_adjustment)
        self.set_rudder(1 if self.get_rudder() > 1 else -1 if self.get_rudder() < -1 else self.get_rudder())
        self.set_heading(
            normalize_angle(self.get_heading() + self.get_max_boat_turn_rate_dps() * elapsed_time * self.get_rudder()))

# For testing
if __name__ == "__main__":
    from island_time import time as island_time
    from test_boat import BoatImpl
    from file_logger import logger, INFO, DEBUG

    log = logger(dest=None)
    log.set_level(DEBUG)

    def test_hard_over_time(boat):
        test_time = island_time()
        start_time = test_time.time()
        interval = 0.5
        while boat.get_rudder() < 1:
            boat.set_commanded_rudder(1)
            boat.update(interval)
            test_time.sleep(interval)
        duration = test_time.time() - start_time
        if duration <= 0.1:
            raise Exception(f"Rudder hard-over took {duration} s which is implausibly fast.")
        if duration > boat.get_hard_over_time_s():
            raise Exception(f"Rudder hard-over took {duration} s and should have completed within {boat.get_hard_over_time_s()} s")
        log.info(f"Hardover completed in {duration} s")

    boat = BoatImpl(Config("../../configuration/config.yaml"))
    boat.set_heading(0)
    boat.set_target_course(100)
    log.debug(f"Testing hardover time. Starting at {boat.get_heading()}, going to {boat.get_target_course()}")
    test_hard_over_time(boat)

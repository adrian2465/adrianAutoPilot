import logging
import time

from math import atan2, pi

from modules.brain import Brain
from modules.common.angle_math import normalize_angle
from modules.common.config import Config
from datetime import datetime
import matplotlib
import matplotlib.pyplot as plt


class BoatSimulator:
    def __init__(self):
        cfg = Config.getConfig()
        self._log = logging.getLogger('BoatSimulator')
        self._compass_deg = 0.0
        self._turn_rate_dps = 0.0
        self._motor_speed = 0.0
        self._rudder_position = 0.0
        self._time_of_last_tick_s = time.time()
        self._rudder_turn_rate_ups = 1000 / float(cfg['rudder_hard_over_time_ms'])

        self._course_tolerance_deg = float(cfg['course_tolerance_deg'])
        self._max_turn_rate_dps = cfg['boat_max_turn_rate_dps']
        self._metric_tolerance = cfg['metric_tolerance']
        self._log.info(f"Rudder max turn rate UPS = {self._rudder_turn_rate_ups}")
        self._log.info(f"Boat max turn rate DPS = {self._max_turn_rate_dps}")
        self._csv_outfile = f"output_{datetime.today().strftime('%Y%m%d_%H%M%S')}_{cfg['pid_gains']['default']}.csv"
        self._start_time = time.time()
        with open(self._csv_outfile, "a") as outfile:
            outfile.write(f"timestamp, rudder, motor, turn_rate, heading\n")

    # Rudder Interface
    def _print_status(self) -> None:
        self._log.info(f"* Messages: {self.hw_messages}")
        self._log.info(f"* Port limit: {self.hw_port_limit}")
        self._log.info(f"* Starboard limit: {self.hw_stbd_limit}")
        self._log.info(f"* HW Rudder position: {self.hw_raw_rudder_position}")
        self._log.info(f"* Normalized Rudder position: {self.rudder_position}")
        self._log.info(f"* Rudder fault: {self.hw_rudder_fault}")
        self._log.info(f"* Raw Motor Speed: {self.hw_raw_motor_speed}")
        self._log.info(f"* Raw Motor Direction: {self.hw_raw_motor_direction}")
        self._log.info(f"* Normalized motor direction: {self.motor_speed}")
        self._log.info(f"* Clutch status: {self.hw_clutch_status}")
        self._log.info(f"* HW Reporting interval (ms): {self.hw_reporting_interval_ms}")
        self._log.info(f"* Echo Status: {self.hw_echo_status}")

    def start_daemon(self) -> None:
        self._log.debug("start_daemon")

    def stop_daemon(self) -> None:
        self._log.debug("stop_daemon")

    def set_clutch(self, status: int) -> None:
        self._log.debug(f"set_clutch {status}")

    @property
    def hw_clutch_status(self):
        return 1

    def set_port_raw_rudder_limit(self, raw_limit: int = None) -> None:
        self._log.debug(f"set_port_raw_rudder_limit {raw_limit}")

    def set_starboard_raw_rudder_limit(self, raw_limit: int = None) -> None:
        self._log.debug(f"set_starboard_raw_rudder_limit {raw_limit}")

    def set_echo_status(self, status) -> None:
        self._log.debug(f"set_echo_status {status}")

    def set_motor_speed(self, normalized_motor_speed) -> None:
        self._log.debug(f"set_motor_speed {normalized_motor_speed}")
        self._motor_speed = normalized_motor_speed

    @property
    def motor_speed(self) -> float:
        self._log.debug(f"Returning motor_speed = {self._motor_speed}")
        return self._motor_speed

    @property
    def rudder_position(self) -> float:
        self._log.debug(f"Returning rudder_position = {self._rudder_position}")
        return self._rudder_position

    # IMU Interface
    @property
    def accel(self):
        self._log.debug("Returning accel = [0, 0, -1]")
        return [0, 0, -1]

    @property
    def gyro(self):
        self._log.error("gyro not implemented in boat simulator")
        return [0, 0, 0]

    @property
    def mag(self):
        self._log.error("mag not implemented in boat simulator")
        return [0, 0, 0]

    @property
    def temp(self):
        self._log.error("temp not implemented in boat simulator")
        return 27

    @property
    def compass_deg(self):
        self._log.debug(f"Returning compass_deg = {self._compass_deg:5.1f}")
        return self._compass_deg

    @property
    def heel_deg(self):
        accel = self.accel
        heel = 180 - (atan2(accel[2], accel[0]) * (180 / pi) + 90 + 360) % 360
        self._log.debug(f"Returning heel_deg = {heel:6.4}")
        return heel

    @property
    def turn_rate_dps(self):
        self._log.debug(f"Returning turn_rate_dps = {self._turn_rate_dps:6.4f}")
        return self._turn_rate_dps

    @property
    def is_running(self):
        self._log.debug(f"Returning is_running = True")
        return True

    # Boat Simulator Interface
    def time_tick(self):
        now_s = time.time()
        time_delta_s = now_s - self._time_of_last_tick_s
        self._time_of_last_tick_s = now_s
        self._log.debug(f"time_tick")
        self._rudder_position = max(-1.0, min(1.0, self._rudder_position +
                                              self._rudder_turn_rate_ups * self._motor_speed * time_delta_s))
        self._turn_rate_dps = self._rudder_position * self._max_turn_rate_dps
        self._compass_deg = normalize_angle(self._compass_deg + self._turn_rate_dps * time_delta_s)

    def print_status(self):
        log.info(f"rudder={self._rudder_position:6.4f} "
                 f"motor={self.motor_speed} "
                 f"turn_rate_dps={self._turn_rate_dps:6.4f} "
                 f"heading={self._compass_deg:5.1f}"
                 )

    def csv_status(self):
        with open(self._csv_outfile, "a") as outfile:
            outfile.write(f"{(time.time() - self._start_time):5.1f}, "
                          f"{self._rudder_position:6.4f}, "
                          f"{self.motor_speed}, "
                          f"{self._turn_rate_dps:6.4f}, "
                          f"{self._compass_deg:5.1f}\n"
                          )


if __name__ == "__main__":
    Config.init()
    initial_heading = 000
    desired_course = 300
    time_limit = 30
    log = logging.getLogger("BoatSimulator.main")
    simulator = BoatSimulator()
    brain = Brain(simulator, simulator)
    brain.course = desired_course
    simulator._compass_deg = initial_heading
    brain.start_daemon()
    time_of_last_print = time.time()
    time_of_last_csv = time.time()
    time_series = []
    rudder_series = []
    course_series = []
    motor_series = []
    rate_of_turn_series = []
    while True:
        now = time.time()
        simulator.time_tick()
        if now - time_of_last_print > 1.0:
            time_of_last_print = now
            simulator.print_status()
        if now - time_of_last_csv > 0.25:
            time_of_last_csv = now
            simulator.csv_status()
            time_series.append(now - simulator._start_time)
            course_series.append(simulator._compass_deg)
            rudder_series.append(simulator._rudder_position)
            motor_series.append(simulator._motor_speed)
            rate_of_turn_series.append(simulator._turn_rate_dps)
        if time_limit <= now - simulator._start_time:
            log.info("Time's up")
            break
        time.sleep(0.1)
    matplotlib.use('MacOSX')
    fig, axs = plt.subplots(4)
    fig.suptitle(simulator._csv_outfile)
    fig.tight_layout()  # Or equivalently,  "plt.tight_layout()"
    axs[0].plot(time_series, course_series)
    axs[0].set_title('heading')
    axs[1].plot(time_series, rate_of_turn_series)
    axs[1].set_title('rate of turn')
    axs[2].plot(time_series, rudder_series)
    axs[2].set_title('rudder pos')
    axs[3].plot(time_series, motor_series)
    axs[3].set_title('motor')
    plt.savefig(f'{simulator._csv_outfile.replace(".csv", ".png")}')
    plt.show()
    log.info("Terminated")
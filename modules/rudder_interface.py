# Adrian Vrouwenvelder
# August 2023
import logging
import threading
import time
from pathlib import Path

import serial

from modules.common.config import Config
from modules.common.hardware_math import motor_to_raw, normalize_rudder, normalize_motor
from modules.common.test_methods import test_equals, test_true

usb_device = "/dev/ttyUSB0"
usb_baud_rate = 115200


class RudderInterface:
    _initialized = False
    def __init__(self):
        config = Config.getConfig()
        self._logger = logging.getLogger("RudderController")
        if not Path(usb_device).exists():
            self.is_unit_test = True
            self._logger.info(f"Running unit tests since {usb_device} is unavailable")
        else:
            if RudderInterface._initialized == True:
                raise RuntimeError("Rudder is being initialized again!")
            RudderInterface._initialized = True
            self.is_unit_test = False
            self._serial = serial.Serial(
                port=usb_device,
                timeout=1,
                baudrate=usb_baud_rate)
            time.sleep(0.2)  # Wait for serial to open
            if not self._serial.is_open:
                raise ConnectionError(f'Port is not open: {usb_device}')
            self._serial.reset_output_buffer()
            self._serial.flushOutput()
            self._logger.info(f'Connected to {usb_device} for sending. Baud={str(self._serial.baudrate)}!')
            self._monitor_thread = threading.Thread(target=self._serial_monitor_daemon)
            self._monitor_thread.daemon = True
            self._is_ready = False
            self._is_killed = False
            self._monitor_read_interval_s = config.get('monitor_read_interval_s', 0.2)
            self._status_report_complete_duration_ms = config.get('status_report_complete_duration_ms', 500)
        self.hw_messages = None
        self.hw_raw_rudder_position = None
        self.hw_rudder_fault = None
        self.hw_raw_motor_direction = None
        self.hw_raw_motor_speed = None
        self.hw_clutch_status = None
        self.hw_echo_status = None
        # Hard stop limit.  Rudder position should always return -1 to 1 despite limits
        self.hw_port_limit = None
        self.hw_stbd_limit = None
        self.hw_reporting_interval_ms = None

    def __str__(self):
        return f"{__class__}(port={self._serial.port} baud={str(self._serial.baudrate)})"

    def __exit__(self):
        _log = self._logger
        self.set_motor_speed(0.0)
        self.set_clutch(0)
        _log.debug("Closing serial interface")
        self._serial.close()
        _log.info("Terminated")

    def _process_message_from_arduino(self, msg):
        _log = self._logger
        if msg.startswith('m='):  # Text message
            self.hw_messages = msg[2:]
        elif msg.startswith('r='):  # Right limit
            self.hw_stbd_limit = int(msg[2:])
        elif msg.startswith('l='):  # Left limit
            self.hw_port_limit = int(msg[2:])
        elif msg.startswith('p='):  # Rudder position magnitude
            self.hw_raw_rudder_position = int(msg[2:])
        elif msg.startswith('x='):  # Rudder position exception (out of bounds)
            self.hw_rudder_fault = int(msg[2:])
        elif msg.startswith('s='):  # Raw Motor speed
            self.hw_raw_motor_speed = int(msg[2:])
        elif msg.startswith('d='):  # Motor direction
            self.hw_raw_motor_direction = int(msg[2:])
        elif msg.startswith('c='):  # Clutch disposition
            self.hw_clutch_status = int(msg[2:])
        elif msg.startswith('i='):
            self.hw_reporting_interval_ms = int(msg[2:])
        elif msg.startswith('e='):
            self.hw_echo_status = int(msg[2:])
        else:
            _log.error(f"Received unsupported message from hardware: '{msg}'")

    def _initialize_hw(self):
        config = Config.getConfig()
        self.set_echo_status(config.get('rudder_echo_status', 0))
        self.set_port_raw_rudder_limit(config.get('rudder_port_limit', 0))
        self.set_starboard_raw_rudder_limit(config.get('rudder_starboard_limit', 1023))
        self._set_hw_reporting_interval_ms(config.get('rudder_reporting_interval_ms', 1000))
        self.set_motor_speed(0)
        self.set_clutch(0)

    def _serial_monitor_daemon(self) -> None:
        _log = logging.getLogger("RudderDaemon")
        self._serial.reset_input_buffer()
        self._serial.flushInput()
        if not self._serial.is_open:
            raise ConnectionError(f'Could not open port {usb_device}')
        self._logger.info(f'Connected to {usb_device} for receiving. Baud={str(self._serial.baudrate)}!')
        self._is_ready = False
        _log.info("asynch serial_monitor started")
        while not self._is_killed:
            time.sleep(self._monitor_read_interval_s)
            try:
                while self._serial.in_waiting > 0:
                    message = self._serial.readline().decode('utf-8').strip()
                    if message != '':
                        _log.debug(f"Processing msg from HW: '{message}'")
                        if message == 'm=REBOOTED':
                            self._is_ready = True
                        self._process_message_from_arduino(msg=message)
            except ValueError as e:
                _log.error(f"Value error! {e}")
            except serial.SerialException as e:
                _log.error(f"Serial Exception {str(e)}")
        _log.info("Arduino monitor exited")
        self._is_ready = False

    def _write(self, msg: str) -> None:
        _log = self._logger
        if not self._serial.is_open:
            _log.error('Port is not open: ' + usb_device)
            return
        try:
            _log.debug(f'sending: "{msg}"')
            self._serial.write((msg + "\n").encode())
        except ValueError:
            _log.error(f"Value error! {msg}")
        except serial.SerialException as e:
            _log.error(f"Serial Exception! {str(e)}")
        except KeyboardInterrupt as e:
            _log.error(f"Keyboard Interrupt {str(e)}")

    def _trigger_status_report(self) -> None:
        self._write("?")

    def _set_hw_reporting_interval_ms(self, v) -> None:
        _log = self._logger
        _log.debug(f"Set set_hw_reporting_interval_ms to {v}")
        self._write(f"i{int(v):04}")

    def _print_status(self) -> None:
        _log = self._logger
        _log.info(f"* Messages: {self.hw_messages}")
        _log.info(f"* Port limit: {self.hw_port_limit}")
        _log.info(f"* Starboard limit: {self.hw_stbd_limit}")
        _log.info(f"* HW Rudder position: {self.hw_raw_rudder_position}")
        _log.info(f"* Normalized Rudder position: {self.rudder_position}")
        _log.info(f"* Rudder fault: {self.hw_rudder_fault}")
        _log.info(f"* Raw Motor Speed: {self.hw_raw_motor_speed}")
        _log.info(f"* Raw Motor Direction: {self.hw_raw_motor_direction}")
        _log.info(f"* Normalized motor direction: {self.motor_speed}")
        _log.info(f"* Clutch status: {self.hw_clutch_status}")
        _log.info(f"* HW Reporting interval (ms): {self.hw_reporting_interval_ms}")
        _log.info(f"* Echo Status: {self.hw_echo_status}")

    def start_daemon(self) -> None:
        _log = self._logger
        _log.info("Starting rudder daemon...")
        self._monitor_thread.start()
        _log.info("Waiting for rudder readiness")
        while not self._is_ready:
            time.sleep(self._monitor_read_interval_s)
        _log.info("Rudder is ready - Sending hardware settings")
        self._initialize_hw()
        self._trigger_status_report()  # Force hardware to report status so all our values get set.
        _log.info("Rudder Daemon is ready for commands")

    def stop_daemon(self) -> None:
        _log = self._logger
        self._is_killed = True
        _log.debug(f"Stop requested")
        self.set_clutch(0)
        self.set_motor_speed(0)
        _log.debug(f"Waiting for death of daemon")
        while self._monitor_thread.is_alive():
            time.sleep(self._monitor_read_interval_s)
        _log.debug(f"Monitor daemon terminated")

    def set_clutch(self, status: int) -> None:
        _log = self._logger
        self._write(f"c{status}")
        while self.hw_clutch_status != status: time.sleep(0.1)

    def set_port_raw_rudder_limit(self, raw_limit: int = None) -> None:
        """Set the port raw limit. 0 <= limit <= 1023. This can be set by turning the rudder to its port limit (minus a bit)
        and then calling this without parameters after waiting a short period to ensure that the hw_raw_rudder_position
        has been registered."""
        _log = self._logger
        if raw_limit is None: raw_limit = self.hw_raw_rudder_position
        self._write(f"l{raw_limit:04}")

    def set_starboard_raw_rudder_limit(self, raw_limit: int = None) -> None:
        """Set the port raw limit. 0 <= limit <= 1023. This can be set by turning the rudder to its stbd limit (minus a bit)
        and then calling this without parameters after waiting a short period to ensure that the hw_raw_rudder_position
        has been registered."""
        _log = self._logger
        if raw_limit is None: raw_limit = self.hw_raw_rudder_position
        self._write(f"r{raw_limit:04}")

    def set_echo_status(self, status) -> None:
        _log = self._logger
        self._write(f"e{status}")

    def set_motor_speed(self, normalized_motor_speed) -> None:
        """
        Motor Speed: -1 <= speed <= 1.  -1 is to port. 1 is to starboard. If motor is turning to port and stbd is
        requested, or vice versa, the motor is first stopped briefly.
        """
        _log = self._logger
        _log.debug(f"Set motor to {normalized_motor_speed}")

        new_raw_direction = 2 if normalized_motor_speed > 0 else 1 if normalized_motor_speed < 0 else 0
        self._write(f"d{new_raw_direction}")
        hw_desired_motor_speed = motor_to_raw(normalized_motor_speed)
        self._write(f"s{hw_desired_motor_speed :03}")
        while self.hw_raw_motor_speed != hw_desired_motor_speed: time.sleep(0.1)

    @property
    def motor_speed(self) -> float:
        """
        Motor Speed: -1 <= speed <= 1.  -1 is to port. 1 is to starboard.
        None if not ready.
        """
        if self.hw_raw_motor_direction is None or self.hw_raw_motor_speed is None:
            return None
        else:
            normalized_motor_direction = -1 if self.hw_raw_motor_direction == 1 \
                else 1 if self.hw_raw_motor_direction == 2 \
                else 0
            return normalized_motor_direction * normalize_motor(self.hw_raw_motor_speed)

    @property
    def rudder_position(self) -> float:
        """Normalized rudder position.  -1<=N<=1.  -1 indicates all the way to port rudder limit, 1 indicates
        all the way to starboard rudder limit.  NOTE: If the starboard rudder limit is 500, then a raw rudder position
        of 500 will yield a normalized rudder position of 1."""
        return normalize_rudder(self.hw_port_limit, self.hw_stbd_limit, self.hw_raw_rudder_position)


def _test_rudder_position_normalization(rudder: RudderInterface) -> None:
    rudder.hw_port_limit = 0
    rudder.hw_stbd_limit = 1023
    rudder.hw_raw_rudder_position = 0
    test_equals(-1.0, rudder.rudder_position)
    rudder.hw_raw_rudder_position = 1023
    test_equals(1.0, rudder.rudder_position)
    rudder.hw_raw_rudder_position = 511.5
    test_equals(0, rudder.rudder_position)
    rudder.hw_port_limit = 100
    rudder.hw_stbd_limit = 923
    rudder.hw_raw_rudder_position = 100
    test_equals(-1.0, rudder.rudder_position)
    rudder.hw_raw_rudder_position = 923
    test_equals(1.0, rudder.rudder_position)
    rudder.hw_raw_rudder_position = 511.5
    test_equals(0, rudder.rudder_position)
    rudder.hw_port_limit = 200
    rudder.hw_raw_rudder_position = 200
    test_equals(-1.0, rudder.rudder_position)
    rudder.hw_raw_rudder_position = 923
    test_equals(1.0, rudder.rudder_position)
    rudder.hw_raw_rudder_position = 525.35
    test_true(abs(-0.09999999 - rudder.rudder_position) < 0.00001, "Failed expected off-center rudder")
    rudder.hw_raw_rudder_position = 561.5
    test_equals(0, rudder.rudder_position)


def _test_motor_speed(rudder: RudderInterface) -> None:
    rudder.hw_raw_motor_speed = 255
    rudder.hw_raw_motor_direction = 0
    test_equals(0, rudder.motor_speed)
    rudder.hw_raw_motor_direction = 1
    test_equals(-1, rudder.motor_speed)
    rudder.hw_raw_motor_direction = 2
    test_equals(1, rudder.motor_speed)
    rudder.hw_raw_motor_speed = 0
    rudder.hw_raw_motor_direction = 2
    test_equals(0, rudder.motor_speed)
    rudder.hw_raw_motor_direction = 1
    test_equals(0, rudder.motor_speed)
    rudder.hw_raw_motor_direction = 0
    test_equals(0, rudder.motor_speed)


if __name__ == "__main__":
    log = logging.getLogger("RudderController.main")
    Config.init()
    rudder = None
    rc = 0
    try:
        rudder = RudderInterface()
        if rudder.is_unit_test:
            _test_rudder_position_normalization(rudder)
            _test_motor_speed(rudder)
        else:
            rudder.start_daemon()
            log.setLevel(logging.ERROR)
            while True:
                try:
                    rudder._print_status()
                    input_str = input("Enter commands (semicolon-separated):\n"
                                      "  Sn = Normalized Motor speed. n = {-1, 0, 1}\n"
                                      "  Cn = Clutch. n={0, 1}\n"
                                      "  En = HW echo. n={0, 1}\n"
                                      "  Lnnnn = Left rudder limit. 0000 <= n <= 1023; Usually less than 512. e.g. L0010\n"
                                      "  Rnnnn = Right rudder limit. 0000 <= n <= 1023; Usually more than 512. e.g. R0923\n"
                                      "  Innnn = Status reporting interval in milliseconds. 0 <= n <= 9999\n"
                                      "  <enter> = status\n>>> ")
                    cmds = input_str.lower().split(";")
                    for cmd in cmds:
                        if cmd.startswith('s'):
                            rudder.set_motor_speed(int(cmd[1:]))
                        elif cmd.startswith('c'):
                            rudder.set_clutch(int(cmd[1:]))
                        elif cmd.startswith('e'):
                            rudder.set_echo_status(int(cmd[1:]))
                        elif cmd.startswith('l'):
                            rudder.set_port_raw_rudder_limit(float(cmd[1:]))
                        elif cmd.startswith('r'):
                            rudder.set_starboard_raw_rudder_limit(float(cmd[1:]))
                        elif cmd.startswith('i'):
                            rudder._set_hw_reporting_interval_ms(int(cmd[1:]))
                        else:
                            rudder._trigger_status_report()
                except KeyboardInterrupt:
                    log.info("Keyboard interrupt")
                    rudder.stop_daemon()
                    rc = 0
                    break
    except ValueError as e:
        log.error(f"Value error! {e}")
        rc = 1
    except serial.SerialException as e:
        log.error(f"Serial Exception! {e}")
        rc = 1
    log.info("Terminated")
    exit(rc)

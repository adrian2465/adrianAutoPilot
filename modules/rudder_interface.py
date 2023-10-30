# Adrian Vrouwenvelder
# August 2023
import logging
import os
import threading
import time
import serial

from modules.common.config import Config
from modules.common.hardware_math import motor_to_arduino, rudder_val_to_arduino, rudder_val_from_arduino, \
    motor_from_arduino

usb_device = "/dev/ttyUSB0"
usb_baud_rate = 115200


class RudderInterface:

    def __init__(self):
        config = Config.getConfig()
        self._logger = logging.getLogger("RudderController")
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
        self._hw_messages = None
        self._hw_rudder_position = None
        self._hw_rudder_fault = None
        self._hw_motor_speed = None
        self._hw_raw_motor_direction = None
        self._hw_raw_motor_speed = None
        self._hw_clutch_status = None
        self._hw_echo_status = None
        self._hw_port_limit = None
        self._hw_stbd_limit = None
        self._hw_reporting_interval_ms = None

    def _initialize_hw(self):
        config = Config.getConfig()
        self.set_echo_status(config.get('rudder_echo_status', 0))
        self.set_port_rudder_limit(config.get('port_rudder_limit', -1))
        self.set_starboard_rudder_limit(config.get('port_rudder_limit', 1))
        self.set_hw_reporting_interval_ms(config.get('rudder_reporting_interval_ms', 1000))
        self.set_motor_speed(0)
        self.set_clutch(0)

    def _serial_monitor_daemon(self) -> None:
        _log = self._logger
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
                        _log.debug(f'received: {message}')
                        if message == 'm=REBOOTED':
                            self._is_ready = True
                        self._process_message_from_arduino(msg=message)
            except ValueError as e:
                _log.error(f"Value error! {e}")
            except serial.SerialException as e:
                _log.error(f"Serial Exception {str(e)}")
        self._is_ready = False
        _log.info("Arduino monitor exited")

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

    def _process_message_from_arduino(self, msg):
        _log = self._logger
        _log.debug(f"Processing msg={msg}")
        if msg.startswith('m='):  # Text message
            self._hw_messages = msg[2:]
        elif msg.startswith('r='):  # Right limit
            self._hw_stbd_limit = rudder_val_from_arduino(int(msg[2:]))
        elif msg.startswith('l='):  # Left limit
            self._hw_port_limit = rudder_val_from_arduino(int(msg[2:]))
        elif msg.startswith('p='):  # Rudder position magnitude
            self._hw_rudder_position = rudder_val_from_arduino(int(msg[2:]))
        elif msg.startswith('x='):  # Rudder position exception (out of bounds)
            v = int(msg[2:])
            self._hw_rudder_fault = 1 if v == 2 else -1 if v == 1 else 0
        elif msg.startswith('s='):  # Motor speed
            self._hw_raw_motor_speed = motor_from_arduino(int(msg[2:]))
        elif msg.startswith('d='):  # Motor direction
            self._hw_raw_motor_direction = -1 if int(msg[2:]) == 1 else 1 if int(msg[2:]) == 2 else 0
        elif msg.startswith('c='):  # Clutch disposition
            self._hw_clutch_status = int(msg[2:])
        elif msg.startswith('i='):
            self._hw_reporting_interval_ms = int(msg[2:])
        elif msg.startswith('e='):
            self._hw_echo_status = int(msg[2:])
        else:
            _log.error(f"Received unsupported message from hardware: '{msg}'")

    def start_daemon(self):
        _log = self._logger
        _log.info("Starting rudder daemon...")
        self._monitor_thread.start()
        _log.info("Waiting for rudder readiness")
        while not self._is_ready:
            time.sleep(self._monitor_read_interval_s)
        _log.info("Rudder is ready - Sending hardware settings")
        self._initialize_hw()
        self.trigger_status_report()  # Force hardware to report status so all our values get set.
        _log.info("Rudder Daemon is ready for commands")

    def stop_daemon(self):
        _log = self._logger
        self._is_killed = True
        _log.debug(f"Stop requested")
        rudder.set_clutch(0)
        rudder.set_motor_speed(0)
        _log.debug(f"Waiting for death of daemon")
        while self._monitor_thread.is_alive():
            time.sleep(self._monitor_read_interval_s)
        _log.debug(f"Monitor daemon terminated")

    def set_clutch(self, status: int):
        self._write(f"c{status}")

    def set_port_rudder_limit(self, limit):
        self._write(f"l{rudder_val_to_arduino(limit):04}")

    def set_starboard_rudder_limit(self, limit):
        self._write(f"r{rudder_val_to_arduino(limit):04}")

    def trigger_status_report(self):
        self._write("?")

    def set_echo_status(self, status):
        _log = self._logger
        self._write(f"e{status}")

    def set_motor_speed(self, normalized_motor_speed):
        """
        Motor Speed: -1 <= speed <= 1.  -1 is to port. 1 is to starboard.
        Internally, also sets direction.
        """
        _log = self._logger
        direction = 1 if normalized_motor_speed > 0 else -1 if normalized_motor_speed < 0 else 0
        self._write(f"d{1 if direction < 0 else 2 if direction > 0 else 0}")
        self._write(f"s{motor_to_arduino(normalized_motor_speed) :03}")

    def set_hw_reporting_interval_ms(self, v):
        self._write(f"i{int(v):04}")

    @property
    def hw_messages(self) -> str:
        """
        Messages from arduino
        None if not ready.
        """
        return self._hw_messages

    @property
    def hw_port_rudder_limit(self):
        return self._hw_port_limit

    @property
    def hw_starboard_rudder_limit(self):
        return self._hw_stbd_limit

    @property
    def hw_rudder_position(self) -> int:
        """
        Rudder position. Sensed by Arduino. Not settable - to move rudder, operate the motor.
        Range is-1 <= rudder_position <= 1, where neg is to port, pos is to starboard.
        None if not ready.
        """
        return self._hw_rudder_position

    @property
    def hw_rudder_fault(self):
        """
        Rudder exceeded stops. Fault. Sent by Arduino. Read-only. Clears when rudder is back within specs.
        Value is 0 if no fault, -1 if rudder exceeded to port, 1 if rudder exceeded to starboard.
        None if not ready.
        """
        return self._hw_rudder_fault

    @property
    def hw_motor_speed(self):
        """
        Motor Speed: -1 <= speed <= 1.  -1 is to port. 1 is to starboard.
        None if not ready.
        """
        if self._hw_raw_motor_direction is None or self._hw_raw_motor_direction is None:
            return None
        else:
            return self._hw_raw_motor_direction * self._hw_raw_motor_direction

    @property
    def hw_clutch_status(self) -> int:
        """
        Status of autopilot.
        0 = disengaged, 1 = engaged
        """
        return self._hw_clutch_status

    @property
    def hw_echo_status(self):
        return self._hw_echo_status

    @property
    def hw_reporting_interval_ms(self):
        return self._hw_reporting_interval_ms

    def __str__(self):
        return f"{__class__}(port={self._serial.port} baud={str(self._serial.baudrate)})"

    def __exit__(self):
        _log = self._logger
        self.set_motor_speed(0.0)
        self.set_clutch(0)
        _log.debug("Closing serial interface")
        self._serial.close()
        _log.info("Terminated")

    def print_status(self):
        _log = self._logger
        _log.info(f"* Messages: {self._hw_messages}")
        _log.info(f"* Port limit: {self._hw_port_limit}")
        _log.info(f"* Starboard limit: {self._hw_stbd_limit}")
        _log.info(f"* Rudder position: {self._hw_rudder_position}")
        _log.info(f"* Rudder fault: {self._hw_rudder_fault}")
        _log.info(f"* Raw Motor Speed: {self._hw_raw_motor_speed}")
        _log.info(f"* Raw Motor Direction: {self._hw_raw_motor_direction}")
        _log.info(f"* Motor speed: {self.hw_motor_speed}")
        _log.info(f"* Clutch status: {self._hw_clutch_status}")
        _log.info(f"* HW Reporting interval (ms): {self._hw_reporting_interval_ms}")
        _log.info(f"* Echo Status: {self._hw_echo_status}")


if __name__ == "__main__":
    log = logging.getLogger("RudderController.main")
    Config.init()
    rudder = None
    rc = 0
    try:
        rudder = RudderInterface()
        rudder.start_daemon()
        log.setLevel(logging.ERROR)
        while True:
            rudder.print_status()
            input_str = input("Enter commands (semicolon-separated):\n"
                              "  Sn = Motor speed. n = {-1, 0, 1}\n"
                              "  Cn = Clutch. n={0, 1}\n"
                              "  En = HW echo. n={0, 1}\n"
                              "  Lnnnn = Left rudder limit. -1 <= n <= 1; typically negative. e.g. L-0.5\n"
                              "  Rnnnn = Right rudder limit. -1 <= n <= 1; typically positive. e.g. R0.5\n"
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
                    rudder.set_port_rudder_limit(float(cmd[1:]))
                elif cmd.startswith('r'):
                    rudder.set_starboard_rudder_limit(float(cmd[1:]))
                elif cmd.startswith('i'):
                    rudder.set_hw_reporting_interval_ms(int(cmd[1:]))
                else:
                    rudder.trigger_status_report()

    except ValueError as e:
        log.error(f"Value error! {e}")
        rc = 1
    except serial.SerialException as e:
        log.error(f"Serial Exception! {e}")
        rc = 1
    except KeyboardInterrupt:
        log.info("Keyboard interrupt")
    if rudder is not None:
        rudder.stop_daemon()
    log.info("Terminated")
    time.sleep(0.5)
    exit(rc)

# Adrian Vrouwenvelder  August 2023
from modules.common.file_logger import Logger
from modules.interfaces.arduino_interface import ArduinoInterface, from_arduino
import time
import serial

_log = Logger("arduino")

class ArduinoSerial(ArduinoInterface):

    def __init__(self):
        super().__init__()
        self._usb = "/dev/ttyUSB0"
        self._baudrate = 115200
        self._debugging = False

        self._serial_out = serial.Serial(
                port=self._usb,
                timeout=1,
                baudrate=self._baudrate)
        time.sleep(0.2)  # Wait for serial to open
        if not self._serial_out.is_open:
            raise Exception(f'ERROR: __init__: Port is not open: ' + self._usb)

        self._serial_out.reset_output_buffer()
        _log.info(f'__init__: {self._serial_out.port} Connected for sending commands at {str(self._serial_out.baudrate)}!')

    def is_debugging(self):
        return self._debugging

    def set_debugging(self, tf):
        self._debugging = tf

    # override
    def serial_monitor(self) -> None:
        _log.info("Arduino started")
        with serial.Serial(
                port=self._usb,
                timeout=1,
                baudrate=self._baudrate) as serial_in:
            serial_in.flushInput()
            time.sleep(0.2)  # Wait for serial to open
            if not serial_in.is_open:
                _log.error('serial_monitor: Could not open port ' + self._usb)
                return
            if not self.is_running():
                _log.warn(": serial_monitor: Not running.")
                return
            _log.info(f': serial_monitor: {serial_in.port} Connected for monitoring at {str(serial_in.baudrate)}!')
            while self.is_running():
                time.sleep(self.check_interval_s)
                try:
                    while serial_in.in_waiting > 0:
                        message = serial_in.readline().decode('utf-8').strip()
                        if message != '':
                            if self.is_debugging():
                                _log.debug(f'received: {message}')
                            from_arduino(interface=self, msg=message)
                except ValueError:
                    _log.error(f"serial_monitor: Value error!")
                except serial.SerialException as e:
                    _log.error(f"serial_monitor: Serial Exception! {str(e)}")
                except KeyboardInterrupt as e:
                    _log.error(f"serial_monitor: Keyboard Interrupt {str(e)}")
        _log.info("Arduino monitor exited")

    # override
    def write(self, msg: str) -> None:
        if not self._serial_out.is_open:
            _log.error('write: Port is not open: ' + self._usb)
            return
        try:
            if self.is_debugging():
                _log.debug(f'sending: "{msg}"')
            self._serial_out.write((msg + "\n").encode())
        except ValueError:
            _log.error(f"write: Value error! {msg}")
        except serial.SerialException as e:
            _log.error(f"write: Serial Exception! {str(e)}")
        except KeyboardInterrupt as e:
            _log.error(f"write: Keyboard Interrupt {str(e)}")

    def __str__(self):
        return f"ArduinoSerialInterface(port={self._serial_out.port} baud={str(self._serial_out.baudrate)})"


# override
def get_interface() -> ArduinoInterface:
    _log.info("ArduinoSerialInterface - used for actual running")
    return ArduinoSerial()


# Adrian Vrouwenvelder  August 2023

from modules.arduinoInterface import ArduinoInterface, from_arduino
import time
import serial
from file_logger import logger, INFO
_log = logger(dest=None)
_log.set_level(INFO)

class ArduinoSerialInterface(ArduinoInterface):

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
    return ArduinoSerialInterface()


# Integration test. Send commands to Arduino and ensure it performs
# as expected
if __name__ == "__main__":
    from time import sleep
    LAG = 1.0
    arduino = get_interface()  # Create monitor and writer.
    arduino.start()  # Start monitor thread
    time.sleep(2)  # Wait for monitor to start up.

    arduino.check_interval_s = 0.2  # TODO THROW EXCEPTION WHEN NOT STARTED
    arduino.set_debugging(True)
    arduino.set_status_interval_ms(int(arduino.check_interval_s * 1000 / 2))
    arduino.set_rudder_limits(-1, 1)

    def verify_equals(expected, actual, message):
        if not actual == expected:
            raise Exception(f"{message}. Expected {expected} but got {actual}")

    def verify_is_basically_equal(expected, actual, message, tolerance=0.01):
        if not abs(actual - expected) <= tolerance:
            raise Exception(f"{message}. Expected {expected} but got {actual}")


    def test_message():
        _log.debug("test_message start")
        verify_equals("Online", arduino.get_message(), "Message is not the expected 'Online'")
        _log.debug("test_message successful.")

    def test_status():
        _log.debug("test_status start")
        arduino.set_clutch(1)
        sleep(LAG)
        verify_equals(1, arduino.clutch(), "Clutch did not engage")
        arduino.set_clutch(0)
        sleep(LAG)
        verify_equals(0, arduino.clutch(), "Clutch did not disengage")
        _log.debug("test_status successful")

    def test_motor():
        _log.debug("test_motor full speed to starboard")
        arduino.set_motor_speed(1.0)
        sleep(2)
        verify_is_basically_equal(1, arduino.motor_speed(), "Motor did not engage to starboard")
        _log.debug("test_motor half speed to starboard")
        arduino.set_motor_speed(0.5)
        sleep(2)
        verify_is_basically_equal(0.5, arduino.motor_speed(), "Motor did not engage to starboard at half speed")
        arduino.set_motor_speed(0.0)  # Stop motor so it doesn't slam from starboard to port
        sleep(0.5)
        _log.debug("test_motor full speed to port")
        arduino.set_motor_speed(-1.0)
        sleep(2)
        verify_is_basically_equal(-1, arduino.motor_speed(), "Motor did not engage to port")
        _log.debug("test_motor - stopping motor")
        arduino.set_motor_speed(0)
        sleep(LAG)
        verify_is_basically_equal(0, arduino.motor_speed(), "Motor did not disengage")
        _log.debug("test_motor successful")

    def test_limits():
        _log.debug("test_limits start")
        port, stbd = arduino.rudder_limits()
        _log.debug("test_limits testing default full range")
        verify_is_basically_equal(-1.0, port, "Port limit wrong")
        verify_is_basically_equal(1.0, stbd, "Starboard limit wrong")
        _log.debug("test_limits testing half range")
        arduino.set_rudder_limits(-0.5, 0.5)
        sleep(LAG)
        port, stbd = arduino.rudder_limits()
        verify_is_basically_equal(-0.5, port, f"Reduced Port limit wrong {port}")
        verify_is_basically_equal(0.5, stbd, f"Reduced Starboard limit wrong {stbd}")
        _log.debug("test_limits testing non-default full range")
        arduino.set_rudder_limits(-1.0, 1.0)
        sleep(LAG)
        port, stbd = arduino.rudder_limits()
        verify_is_basically_equal(-1.0, port, "Port limit could not be reset to default")
        verify_is_basically_equal(1.0, stbd, "Starboard limit could not be reset to default")
        _log.debug("test_limits successful")

    def test_rudder_fault():
        _log.debug("test_rudder_fault start")
        arduino.set_motor_speed(1.0)
        sleep(2)
        f = arduino.rudder_fault()
        verify_equals(0, f, f"Rudder fault {f} without limit constraint")
        _log.debug("test_rudder_fault testing ridiculously narrow band to starboard - Motor should stop")
        arduino.set_rudder_limits(0.9, 1.0)  # Excessive constraint should fault to port.
        sleep(LAG)
        f = arduino.rudder_fault()
        verify_equals(-1, f, f"Rudder fault {f} with excessive port constraint")
        _log.debug("test_rudder_fault testing ridiculously narrow band to port - Motor should stop")
        arduino.set_rudder_limits(-1.0, -0.9)  # Excessive constraint should fault to starboard.
        sleep(LAG)
        f = arduino.rudder_fault()
        verify_equals(1, f, f"Rudder fault {f} with excessive stbd constraint")
        _log.debug("test_rudder_fault testing normal range - motor should restart, fault should clear")
        arduino.set_rudder_limits(-1.0, 1.0)
        sleep(LAG)
        f = arduino.rudder_fault()
        verify_equals(0, f, f"Rudder fault {f} without limit constraint after reset")
        sleep(2)
        _log.debug("test_rudder_fault - Stopping motor after rudder fault test.")
        arduino.set_motor_speed(0.0)
        sleep(LAG)
        _log.debug("test_rudder_fault successful")

    try:
        test_message()
        test_status()
        test_motor()
        test_limits()
        test_rudder_fault() # NOTE: Can't test rudder fault until position pin is hooked up.
    except Exception as e:
        _log.error(f"Exception {e}")
    finally:
        arduino.stop()
        sleep(2)  # Give monitor time to die
        _log.debug("ArduinoSerialInterface Tests Exited.")
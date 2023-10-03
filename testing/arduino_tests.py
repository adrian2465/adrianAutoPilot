from modules.real.arduino_serial import get_interface
from modules.common.file_logger import Logger
import time

_log = Logger(config_path="arduino", dest=None, who="arduinoSerialTester")

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
        arduino.set_motor(1.0)
        sleep(2)
        verify_is_basically_equal(1, arduino.motor(), "Motor did not engage to starboard")
        _log.debug("test_motor half speed to starboard")
        arduino.set_motor(0.5)
        sleep(2)
        verify_is_basically_equal(0.5, arduino.motor(), "Motor did not engage to starboard at half speed")
        arduino.set_motor(0.0)  # Stop motor so it doesn't slam from starboard to port
        sleep(0.5)
        _log.debug("test_motor full speed to port")
        arduino.set_motor(-1.0)
        sleep(2)
        verify_is_basically_equal(-1, arduino.motor(), "Motor did not engage to port")
        _log.debug("test_motor - stopping motor")
        arduino.set_motor(0)
        sleep(LAG)
        verify_is_basically_equal(0, arduino.motor(), "Motor did not disengage")
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
        arduino.set_motor(1.0)
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
        arduino.set_motor(0.0)
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

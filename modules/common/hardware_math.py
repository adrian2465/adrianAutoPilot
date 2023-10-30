# Author: Adrian Vrouwenvelder
# October 2023
import logging
from ctypes import c_short  # for signed int. c_short is 16 bits, signed (-32768 to 32767)

from modules.common.config import Config
from modules.common.test_methods import test_equals


def rudder_val_from_arduino(v):
    """
    Normalize a rudder value received from the arduino
    Mapping: 0 <= v <= 1023 :: -1 <= rc <= 1
    :return: normalized value  -1 to 1
    """
    return v / 512 - 1


def rudder_val_to_arduino(v):
    """
    Encode a normalized rudder to a rudder value to be sent to the arduino
    Mapping: -1 <= v <= 1 :: 0 <= rc <= 1023
    :return: 0 - 1023 rudder value to send to arduino
    """
    return int((512 - 0.5) * (v + 1))


def motor_from_arduino(v):
    """
    Normalize a motor speed value received from the arduino
    Mapping: 0 <= v <= 255 :: 0 <= rc <= 1
    NOTE: No direction is included.
    :return: normalized value 0 to 1
    """
    # return v / 255 # For variable voltage motor
    return 1 if v >= 127 else 0


def motor_to_arduino(v):
    """
    Encode a normalized motor value to a motor speed to be sent to arduino
    Mapping: 0 <= |v| <= 1 :: 0 <= rc <= 255
    :return: 0 - 255 motor speed to send to arduino
    """
    # return int(255 * v)  # For variable voltage motor
    return 255 if abs(v) >= 0.5 else 0


def c_short_from_big_endian(msb, lsb):
    """Convert big endian bytes to c_short."""
    return c_short(lsb | (msb << 8)).value


def c_short_from_little_endian(msb, lsb):
    """Convert little endian bytes to c_short."""
    return c_short(msb | (lsb << 8)).value


if __name__ == "__main__":
    Config.init()
    logger = logging.getLogger("hardware_math_test")

    test_equals(1, round(rudder_val_from_arduino(1023), 2))
    test_equals(-1, round(rudder_val_from_arduino(0), 2))
    test_equals(0, round(rudder_val_from_arduino(512), 2))
    test_equals(0, rudder_val_to_arduino(-1))

    test_equals(1023, rudder_val_to_arduino(1))
    test_equals(511, rudder_val_to_arduino(0))

    test_equals(1, motor_from_arduino(255))
    test_equals(0, motor_from_arduino(0))
    test_equals(1, motor_from_arduino(127))
    test_equals(0, motor_from_arduino(126))

    test_equals(255, motor_to_arduino(0.98))
    test_equals(0, motor_to_arduino(0.02))

    test_equals(32000, c_short_from_big_endian(0x7d, 0x00))
    test_equals(32000, c_short_from_little_endian(0x00, 0x7d))

    logger.info("All tests passed")
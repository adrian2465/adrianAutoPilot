# Adrian Vrouwenvelder
# August 2023
import logging
from ctypes import c_short  # for signed int. c_short is 16 bits, signed (-32768 to 32767)

from modules.common.config import Config
from modules.common.test_methods import test_equals, test_true, test_none


def normalize_rudder(hw_port_limit: int, hw_stbd_limit: int, hw_pos: int) -> float:
    """
    Normalize a rudder value received from the arduino
    Mapping: 0 <= v <= 1023 :: -1 <= rc <= 1
    :return: normalized value  -1 to 1
    """
    if hw_port_limit is None or hw_stbd_limit is None or hw_pos is None: return None
    if hw_port_limit >= hw_stbd_limit: raise ValueError("Port limit must be less than starboard limit")
    ctr = float(hw_stbd_limit + hw_port_limit) / 2.0
    return (float(hw_pos) - ctr) / float(hw_stbd_limit - ctr)


def normalize_direction(v_raw: int) -> float:
    """
    Normalize a direction value received from the arduino
    Mapping: v = {0=Center, 1=Port, 2=Starboard} => -1 <= rc <= 1
    :return: normalized value -1 to 1
    """
    return 0.0 if is_within(v_raw, 0, 0.0001) else -1.0 if v_raw == 1 else 1.0


def direction_to_raw(v_norm: float) -> int:
    """Encode a normalized rudder direction to a value to be sent to the arduino
    Mapping: -1 <= v <= 1 => rc = {0=Center, 1=Port, 2=Starboard}
    """
    return 0 if is_within(v_norm, 0.0, 0.0001) else 1 if v_norm < 0.0 else 2


def normalize_motor(raw_v: int) -> int:
    """
    Normalize a motor speed value received from the arduino
    Mapping: 0 <= v <= 255 :: 0 <= rc <= 1
    NOTE: No direction is included
    :return: normalized value 0 to 1
    """
    # return v / 255 # For variable voltage motor
    return 1 if raw_v >= 127 else 0


def motor_to_raw(norm_v: float) -> int:
    """
    Encode a normalized motor value to a motor speed to be sent to arduino
    Mapping: 0 <= |v| <= 1 :: 0 <= rc <= 255
    :return: 0 - 255 motor speed to send to arduino
    """
    # return int(255 * v)  # For variable voltage motor
    return 0 if is_within(norm_v, 0.0, 0.1) else 255


def c_short_from_big_endian(msb: int, lsb: int) -> int:
    """Convert big endian bytes to c_short."""
    return c_short(lsb | (msb << 8)).value


def c_short_from_little_endian(msb: int, lsb: int) -> int:
    """Convert little endian bytes to c_short."""
    return c_short(msb | (lsb << 8)).value


def is_within(v1: float, v2: float, tolerance: float) -> bool:
    return abs(v1-v2) <= tolerance


if __name__ == "__main__":
    Config.init()
    logger = logging.getLogger("hardware_math_test")

    test_none(normalize_rudder(None, 1023, 1023))
    test_none(normalize_rudder(1023, None, 1023))
    test_none(normalize_rudder(1023, 1023, None))
    test_equals(1, round(normalize_rudder(0, 1023, 1023), 2))
    test_equals(-1, round(normalize_rudder(0, 1023, 0), 2))
    test_equals(0, round(normalize_rudder(0, 1023, 512), 2))

    test_equals(-1.0, normalize_rudder(0, 1023, 0))
    test_equals(1.0, normalize_rudder(0, 1023, 1023))
    test_equals(0, normalize_rudder(0, 1023, 511.5))
    test_equals(-1.0, normalize_rudder(100, 923, 100))
    test_equals(1.0, normalize_rudder(100, 923, 923))
    test_equals(0, normalize_rudder(100, 923, 511.5))
    test_equals(-1.0, normalize_rudder(200, 923, 200))
    test_equals(1.0, normalize_rudder(200, 923, 923))
    test_true(abs(-0.09999999 - normalize_rudder(200, 923, 525.35)) < 0.00001, "Failed expected off-center rudder")
    test_equals(0, normalize_rudder(200, 923, 561.5))

    test_equals(1, normalize_motor(255))
    test_equals(0, normalize_motor(0))
    test_equals(1, normalize_motor(127))
    test_equals(0, normalize_motor(126))

    test_equals(255, motor_to_raw(0.98))
    test_equals(0, motor_to_raw(0.00002))

    test_equals(32000, c_short_from_big_endian(0x7d, 0x00))
    test_equals(32000, c_short_from_little_endian(0x00, 0x7d))

    test_equals(1, normalize_direction(2))
    test_equals(-1, normalize_direction(1))
    test_equals(0, normalize_direction(0))

    test_equals(2, direction_to_raw(1))
    test_equals(1, direction_to_raw(-1))
    test_equals(0, direction_to_raw(0))

    test_true(is_within(1.1, 1.2, .1), "1.1 != 1.2 with tolerance of 0.1 - is_within should be true")
    test_true(not is_within(1.1, 1.2, .01), "1.1 == 1.2 with tolerance of 0.01 - is_within should be false")

    logger.info("All tests passed")
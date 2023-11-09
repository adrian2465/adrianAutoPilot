# Adrian Vrouwenvelder
# August 2023

import logging

from modules.common.config import Config
from modules.common.test_methods import test_equals, test_true


def is_on_course(course, heading, course_tolerance_deg):
    return abs(calculate_acute_angle(course, heading)) <= course_tolerance_deg


def normalize_angle(angle):
    """Return angle corrected to lie between 0 and 359 degrees, inclusive. """
    return angle % 360


def calculate_acute_angle(angle1, angle2):
    """Return acute angle between two vectors. Always between -180 and 180, inclusive.
    If the acute angle (shortest way from angle1 to angle2) is formed by going clockwise from angle1 to angle2,
    the result will be positive; otherwise the result will be negative."""
    diff = (angle2 - angle1 + 180) % 360 - 180
    return (diff + 360) if diff < -180 else diff


def celsius_to_fahrenheit(c):
    """Convert celsius to fahenheit temperature."""
    return c * 9.0 / 5.0 + 32.0


def vector_from(data, address, bias, endian_transformer_fn):
    """Extract a vector from an MPU data array."""
    return [endian_transformer_fn(data[0 + address], data[1 + address]) * bias,
            endian_transformer_fn(data[2 + address], data[3 + address]) * bias,
            endian_transformer_fn(data[4 + address], data[5 + address]) * bias]


def apply_operation(operation, vector1, vector2):
    """Apply a binary operation to two vectors of the same length. I.e. A + B = [a0+b0, a1+b1, a2+b2, ...]"""
    if len(vector1) != len(vector2):
        raise ValueError(f"{vector1} and {vector2} are not the same length")
    result_vector = [0] * len(vector1)
    for i, d in enumerate(vector1):
        result_vector[i] = operation(d, vector2[i])
    return result_vector


if __name__ == "__main__":
    Config.init()
    logger = logging.getLogger("angle_math_test")
    logger.info("Testing angle normalizer")
    test_equals(5, normalize_angle(365))
    test_equals(355, normalize_angle(-5))
    test_equals(0, normalize_angle(-360))
    test_equals(0, normalize_angle(360))
    test_equals(180, normalize_angle(180))
    logger.info("Testing angle difference calculation")
    test_equals(100, calculate_acute_angle(100, 200))
    test_equals(-101, calculate_acute_angle(200, 99))
    test_equals(-102, calculate_acute_angle(0, 258))
    test_equals(110, calculate_acute_angle(260, 10))
    test_equals(179, calculate_acute_angle(90, 269))  # Interior angle includes bottom of circle
    test_equals(-179, calculate_acute_angle(90, 271))  # Interior angle includes top of circle
    test_equals(179, calculate_acute_angle(271, 90))
    test_equals(-179, calculate_acute_angle(269, 90))
    logger.info("Testing is_on_course")
    test_true(is_on_course(100, 100.5, 0.6), "Should be on course but is not")
    test_true(not is_on_course(100, 100.5, 0.4), "Should not be on course, but is")
    logger.info("Testing C->F temperature conversions")
    test_equals(32, celsius_to_fahrenheit(0))
    test_equals(212, celsius_to_fahrenheit(100))
    logger.info("Testing vector-from-data extractor")
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    test_equals([3.0, 7.0, 11.0],
                vector_from(data=data,
                            address=0,
                            bias=1.0,
                            endian_transformer_fn=lambda x, y: x + y))
    test_equals([30.0, 38.0, 46.0],
                vector_from(data=data,
                            address=6,
                            bias=2.0,
                            endian_transformer_fn=lambda x, y: x + y))
    logger.info("Testing vector operation applier")
    test_equals([5, 7, 9], apply_operation(lambda a, b: a + b, [1, 2, 3], [4, 5, 6]))
    try:
        apply_operation(lambda a, b: a + b, [1, 2, 3], [4, 6])
        raise Exception("Vectors of different length did not raise exception")
    except ValueError:
        pass
    logger.info("All tests passed")

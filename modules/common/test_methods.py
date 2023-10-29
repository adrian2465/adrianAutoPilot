# Author: Adrian Vrouwenvelder
# October 2023

def test_vectors_equal(expected, actual):
    if len(expected) != len(actual): raise Exception(f"expected {expected} but got {actual}")
    for i in range(len(expected)):
        if expected[i] != actual[i]: raise Exception(f"expected {expected} but got {actual}")


def test_equals(expected, actual):
    if actual != expected: raise Exception(f"expected {expected} but got {actual}")


def test_true(condition, message):
    if not condition: raise Exception(message)

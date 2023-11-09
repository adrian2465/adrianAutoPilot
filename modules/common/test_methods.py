# Adrian Vrouwenvelder
# August 2023


import collections.abc


def test_equals(expected, actual) -> None:
    if isinstance(expected, collections.abc.Sequence):
        if len(expected) != len(actual): raise Exception(f"expected length {len(expected)} but got {len(actual)}")
        for i in range(len(expected)):
            if expected[i] != actual[i]: raise Exception(f"expected {expected} but got {actual}")
    else:
        if actual != expected: raise Exception(f"expected {expected} but got {actual}")


def test_true(condition, message) -> None:
    if not condition: raise Exception(message)


def test_none(value) -> None:
    if value is not None: raise Exception(f"Expected None but got {value}")
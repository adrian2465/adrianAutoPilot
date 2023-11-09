# Adrian Vrouwenvelder
# August 2023
import logging

from modules.common.config import Config
from modules.common.test_methods import test_equals


class WeightedAverageVector:

    def __init__(self, weight):
        self._average_vector = None
        self._weight = weight

    def add(self, vector):
        if self._average_vector is None:
            self._average_vector = vector
        else:
            if len(vector) != len(self._average_vector):
                raise ValueError(f"Vectors {len(self._average_vector)} and {len(vector)} must be of equal length")

            self._average_vector = [(vector[i] + self._average_vector[i] * (self._weight - 1)) / self._weight
                                    for i in range(0, len(vector))]
        return self

    @property
    def value(self):
        return self._average_vector


if __name__ == "__main__":
    Config.init()
    logger = logging.getLogger("wav_test")
    mav = WeightedAverageVector(5)\
        .add([2, 4, 6])\
        .add([2, 4, 6])\
        .add([2, 4, 6])\
        .add([2, 4, 6])\
        .add([2, 4, 6])\
        .add([2, 4, 6])
    test_equals([2, 4, 6], mav.value)
    mav.add([4, 8, 12])
    test_equals([2.4, 4.8, 7.2], mav.value)
    try:
        mav.add([1])
        raise Exception("Test failed - expected exception")
    except ValueError:
        pass
    logger.info("All tests passed")

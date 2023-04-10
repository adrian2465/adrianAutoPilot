# Author: Adrian Vrouwenvelder
# April 9, 2023
import yaml

class Config:

    def __init__(self, filename):
        self._gains = None
        self._boat_characteristics = None
        with open(filename, 'r') as stream:
            data = yaml.safe_load(stream)
            self._boat_characteristics = data["boat_characteristics"]
            self._gains = data["gains"]
            self._mpu = data["mpu9250"]

    @property
    def gains(self):
        return self._gains

    @property
    def boat(self):
        return self._boat_characteristics

    @property
    def mpu(self):
        return self._mpu

# TODO Revisit places thqat use config
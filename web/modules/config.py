# Author: Adrian Vrouwenvelder
# April 9, 2023
import yaml


class Config:

    def __init__(self, filename):
        with open(filename, 'r') as stream:
            data = yaml.safe_load(stream)
            self._pid = data["pid"]
            self._boat = data["boat"]
            self._brain = data["brain"]
            self._mpu = data["mpu9250"]
            self._arduino = data["arduino"]

    @property
    def pid(self):
        return self._pid

    @property
    def boat(self):
        return self._boat

    @property
    def brain(self):
        return self._brain

    @property
    def mpu(self):
        return self._mpu

    @property
    def arduino(self):
        return self._arduino

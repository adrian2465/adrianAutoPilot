# Author: Adrian Vrouwenvelder
import time as real_time

class time: 

    _timetick = 1

    def set_elapsed_time(self,t):
        self._timetick = t

    def time(self):
        return time._timetick

    def sleep(self, secs):
        time._timetick = time._timetick + secs

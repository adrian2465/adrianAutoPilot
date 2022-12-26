# Author: Adrian Vrouwenvelder
import time as real_time

class time: 

    _timetick = 0

    def time():
        return time._timetick

    def sleep(secs):
        time._timetick = time._timetick + secs

#    def time():
#        return real_time.time()
#
#    def sleep(secs):
#        real_time.sleep(secs)

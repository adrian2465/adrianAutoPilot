import time as real_time

class time: 

    def time():
        return real_time.time()*1000

    def sleep(secs):
        real_time.sleep(secs/1000)
#    def time():
#        return real_time.time()
#
#    def sleep(secs):
#        real_time.sleep(secs)

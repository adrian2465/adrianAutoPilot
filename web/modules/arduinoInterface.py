## Adrian Vrouwenvelder
## December 1, 2022

import threading
import time

# Private
class ArduinoInterface():
    def __init__(self):
        self._monitor_thread = threading.Thread(target = self.serial_monitor)
        self._monitor_thread.daemon = True
        self._check_interval = 1
        self._running = False
        self._from_arduino = NotImplemented
    def start(self):
        self._running = True
        self._monitor_thread.start()
    def stop(self):
        self._running = False
    def check_interval(self):
        return self._check_interval
    def isRunning(self):
        return self._running
    def setFromArduino(self, from_arduino):
        self._from_arduino = from_arduino

    #override this
    def serial_monitor(self) -> str:
        # Implement this
        k = 0
        while True:
          self._from_arduino(msg=f"publishing {k}")
          k = k + 1
          time.sleep(1)

    #override this
    def write(self, msg: str) -> None:
        print(f"ArduinoInterface.write({msg})")

#override factory method
def getInterface():
    return ArduinoInterface()

################################################################################
# For testing and exemplification
def testBrain():

    def from_arduino(msg): 
        # Put just enough processing here to communicate with brain loop.
        print(f"Brain Received '{msg}'")

    arduino = getInterface() # Create monitor and writer.
    arduino.setFromArduino(from_arduino)
    arduino.start() # Start monitor thread
    k = 0
    while k < 5:
        time.sleep(4)
        arduino.write(f"{k}")
        k = k + 1
    print("Stopped.")

if __name__ == "__main__":
    testBrain()
    
#Brain Received 'publishing 0'
#Brain Received 'publishing 1'
#Brain Received 'publishing 2'
#Brain Received 'publishing 3'
#ArduinoInterface.write(0)
#Brain Received 'publishing 4'
#Brain Received 'publishing 5'
#Brain Received 'publishing 6'
#Brain Received 'publishing 7'
#ArduinoInterface.write(1)
#Brain Received 'publishing 8'
#Brain Received 'publishing 9'
#Brain Received 'publishing 10'
#Brain Received 'publishing 11'
#ArduinoInterface.write(2)
#Brain Received 'publishing 12'

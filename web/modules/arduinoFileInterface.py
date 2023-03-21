## Adrian Vrouwenvelder
## December 1, 2022

from modules.arduinoInterface import ArduinoInterface, from_arduino
from pathlib import Path
import time

fromArduinoFile="/tmp/fromArduino.txt"
toArduinoFile="/tmp/toArduino.txt"

# Private
class ArduinoFileInterface(ArduinoInterface):
    #override
    def serial_monitor(self) -> str: 
        while (self.is_running()):
            my_file = Path(fromArduinoFile)
            if my_file.is_file():
                with open(fromArduinoFile) as openfileobject:
                    for line in openfileobject:
                        from_arduino(interface=self, msg=line)
                open(fromArduinoFile, 'w').close() # Delete contents
            time.sleep(self.get_check_interval())

    #override
    def write(self, msg: str) -> None:
        # Append-adds at last
        with open(toArduinoFile, "a") as openfileobject:
           openfileobject.write(msg)

#override
def getInterface():
    return ArduinoFileInterface()

################################################################################
# For testing and exemplification
def cmd_line():
    # Sample class for subscribing to arduino events.
    def from_arduino(msg): 
        # Put just enough processing here to communicate with brain loop.
        print(f"fromArduino: '{msg}'")

    arduino = getInterface() # Create monitor and writer.
    arduino.start() # Start monitor thread
    print(f'Append commands to {fromArduinoFile} to simulate Arduino sending data')
    print(f'From a command prompt, monitor {toArduinoFile} to see data we\'re sending to the Arduino.')
    while True:
        cmd = input("Enter command to send to arduino(x=exit):")
        if cmd == 'x': break;
        arduino.write(cmd)
    arduino.stop()
    print("Stopped.")

if __name__ == "__main__":
    cmd_line()

## Adrian Vrouwenvelder
## December 1, 2022

from modules.arduinoInterface import ArduinoInterface, from_arduino
from pathlib import Path
from file_logger import logger, DEBUG
import time

_from_arduino_filename = "/tmp/fromArduino.txt"
_to_arduino_filename = "/tmp/toArduino.txt"
_log = logger(dest=None)
_log.set_level(DEBUG)


class ArduinoFileInterface(ArduinoInterface):
    # override
    def serial_monitor(self) -> str:
        _log.info(f"arduinoFileInterface ({self}) serial monitor is alive")
        while self.is_running:
            my_file = Path(_from_arduino_filename)
            if my_file.is_file():
                with open(_from_arduino_filename) as from_arduino_file:
                    for line in from_arduino_file:
                        _log.debug(f"Processing line from arduino: {line}")
                        from_arduino(interface=self, msg=line)
                open(_from_arduino_filename, 'w').close()  # Delete contents
            time.sleep(self.check_interval_s)
        _log.info(f"arduinoFileInterface serial monitor terminated")

    # override
    def write(self, msg: str) -> None:
        # Append-adds at last
        with open(_to_arduino_filename, "a") as to_arduino_file:
            to_arduino_file.write(f"{msg}\n")

    # def __str__(self):
    #     return f"ArduinoFileInterface({_from_arduino_filename}, {_to_arduino_filename})"


def get_interface():
    _log.info("ArduinoFileInterface - used for simulation")
    _log.info(f"BRAIN <===  ARDUINO: echo -n \"c=1\" >> {_from_arduino_filename}")
    _log.info(f"BRAIN  ===> ARDUINO: tail -f {_to_arduino_filename}")
    return ArduinoFileInterface()


if __name__ == "__main__":
    # Sample class for subscribing to arduino events.
    def from_arduino(interface, msg):
        _log.info(f"Received from Arduino: '{msg}' on interface {interface}")


    arduino = get_interface()  # Create monitor and writer.
    arduino.start()  # Start monitor thread
    while True:
        cmd = input("Enter command to send to arduino(x=exit):")
        if cmd == 'x':
            break
        arduino.write(cmd)
    arduino.stop()
    _log.info("Stopped.")

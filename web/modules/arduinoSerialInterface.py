## Adrian Vrouwenvelder
## March 21, 2023

from modules.arduinoInterface import ArduinoInterface, from_arduino
import time
import serial

class ArduinoSerialInterface(ArduinoInterface):

    def __init__(self):
        super().__init__()
        self._usb = "/dev/ttyUSB0"
        self._baudrate = 115200
        self._serial_out = serial.Serial(
                port=self._usb,
                timeout=1,
                baudrate=self._baudrate)
        time.sleep(0.2)  # Wait for serial to open
        if not self._serial_out.is_open:
            print('ERROR: __init__: Port is not open: ' + self._usb)
        else:
            self._serial_out.reset_output_buffer()
            print(f'INFO: __init__: {self._serial_out.port} Connected for sending commands at {str(self._serial_out.baudrate)}!')


    #override
    def serial_monitor(self) -> None:
        with serial.Serial(
                port=self._usb,
                timeout=1,
                baudrate=self._baudrate) as serial_in:
            serial_in.flushInput()
            time.sleep(0.2)  # Wait for serial to open
            if not serial_in.is_open:
                print('ERROR: serial_monitor: Could not open port ' + self._usb)
                return
            if not self.is_running():
                print("WARNING: serial_monitor: Not running.")
                return
            print(f'INFO: serial_monitor: {serial_in.port} Connected for monitoring at {str(serial_in.baudrate)}!')
            while (self.is_running()):
                time.sleep(self.get_check_interval())
                try:
                    while serial_in.in_waiting > 0:
                        message = serial_in.readline().decode('utf-8').strip()
                        if message != '':
                            from_arduino(interface=self, msg=message)
                except ValueError:
                    print(f"ERROR: serial_monitor: Value error!")
                except serial.SerialException as e:
                    print(f"ERROR: serial_monitor: Serial Exception! {str(e)}")
                except KeyboardInterrupt as e:
                    print(f"ERROR: serial_monitor: Keyboard Interrupt {str(e)}")

    #override
    def write(self, msg: str) -> None:
        if not self._serial_out.is_open:
            print('ERROR: write: Port is not open: ' + self._usb)
            return
        try:
            self._serial_out.write((msg + "\n").encode())
        except ValueError:
            print(f"ERROR: write: Value error! {msg}")
        except serial.SerialException as e:
            print(f"ERROR: write: Serial Exception! {str(e)}")
        except KeyboardInterrupt as e:
            print(f"ERROR: write: Keyboard Interrupt {str(e)}")

#override
def getInterface():
    return ArduinoSerialInterface()

################################################################################
# For testing and exemplification
def cmd_line():

    arduino = getInterface()  # Create monitor and writer.
    arduino.start()  # Start monitor thread
    print(f'Append commands to arduino to simulate Arduino sending data')
    print(f'From a command prompt, monitor arduino to see data we\'re sending to the Arduino.')
    while True:
        cmd = input("Enter command to send to arduino(x=exit):")
        if cmd == 'x':
            break
        arduino.write(cmd)
    arduino.stop()
    print("Stopped.")

if __name__ == "__main__":
    cmd_line()

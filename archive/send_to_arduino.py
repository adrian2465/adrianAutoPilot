# "Console" for sending messages to the Arduino. 
import serial
import time

usb = "/dev/ttyUSB0"

if __name__ == '__main__':
    print('Press ctrl-C to exit')
    with serial.Serial(
            port=usb,
            timeout=1,
            baudrate=115200) as dev_arduino:
        time.sleep(0.2)  # Wait for serial to open
        if not dev_arduino.is_open:
            print('Could not open port ' + usb)
            exit(1)
        dev_arduino.reset_output_buffer()
        print(f'{dev_arduino.port} Connected!')
        print('Commands (can be separated with semicolons):')
        print('  sleep: (Not sent to arduino) - sleeps for 0.05s. Concatenate to extend sleep.')
        print('  cn: Clutch. n=0:off; n=1:on')
        print('  dn: Motor direction. n=0:neither; n=1:left; n=2:right')
        print('  snnn: Speed. nnn=000:off; nnn=255:max')
        print('  lnnnn: Left limit. 0000 <= nnnn <= 1023')
        print('  rnnnn: Right limit. 0000 <= nnnn <= 1023')
        print('  innnn: Status interval (ms). i0010 means 10ms. 1000 means 1s.')
        print('e.g. d1;sleep;sleep;sleep;d0')
        try:
            while True:
                input_str = input("Enter command:")
                cmds = input_str.split(";")
                for cmd in cmds:
                    if cmd.startswith("sleep"):
                      time.sleep(0.05)
                      continue
                    dev_arduino.write((cmd + "\n").encode())
        except ValueError:
            print("Value error!")
            exit(1)
        except serial.SerialException:
            print("Serial Exception!")
            exit(1)
        except KeyboardInterrupt:
            print("Keyboard Interrupt")
            exit(0)
        else:
            exit(0)
        finally:
            print("Terminated")
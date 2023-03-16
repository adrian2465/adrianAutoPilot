# "Console" for monitoring communications from the Arduino. 
# Can be run in background - pipe output to /dev/tty0
import serial
import fcntl
import time

usb = "/dev/ttyUSB0"

if __name__ == '__main__':
  print('Running.')
  with  serial.Serial(
        port=usb, 
        timeout=1,
        baudrate=115200) as dev_arduino:
    dev_arduino.flushInput()
    time.sleep(0.2) # Wait for serial to open
    if not dev_arduino.is_open(): 
      print('Could not open port ' + usb)
      exit(1)
    print(f'{dev_arduino.port} Connected!')
    try:
      while True:
        while dev_arduino.in_waiting > 0:
          message = dev_arduino.readline().decode('utf-8').strip()
          if message != '': print(message)
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

import serial
import time
if __name__ == '__main__':
  print('Running. Press ctrl-C to exit')
  with serial.Serial(
      port="/dev/ttyUSB0", 
      baudrate=9600,
      rtscts=True,
      timeout=0) as arduino:
    time.sleep(0.2) # Wait for serial to open
    if not arduino.isOpen(): 
      print('Could not open port.')
      exit()
    print(f'{arduino.port} Connected!')
    try:
      while True:
        message = ''
        while arduino.in_waiting > 0:
          c = arduino.read(1)
          if c == '\x00': continue
          message = message + str(c)

        if len(message) > 0: print(message)
    except KeyboardInterrupt:
      print("Keyboard Interrupt")

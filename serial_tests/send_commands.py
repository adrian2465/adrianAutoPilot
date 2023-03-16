import serial
import time
if __name__ == '__main__':
  print('Running. Press ctrl-C to exit')
  with serial.Serial("/dev/ttyUSB0", 115200, timeout=1) as arduino:
    time.sleep(0.2) # Wait for serial to open
    if not arduino.isOpen(): 
      print('Could not open port.')
      exit()
    print(f'{arduino.port} Connected!')
    print('Commands:')
    print('  cn: Clutch. n=0:off; n=1:on')
    print('  dn: Motor direction. n=0:neither; n=1:left; n=2:right')
    print('  snnn: Speed. nnn=000:off; nnn=255:max')
    print('  lnnnn: Left limit. 0000 <= nnnn <= 9999')
    print('  rnnnn: Right limit. 0000 <= nnnn <= 9999')
    print('  innnn: Status interval (ms). i0010 means 10ms.')
    try:
      while True:
        cmd = input("Enter command: ")
        cmd = cmd + "\n"
        arduino.write(cmd.encode())
    except KeyboardInterrupt:
      print("Keyboard Interrupt")

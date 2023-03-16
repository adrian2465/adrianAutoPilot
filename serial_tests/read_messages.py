import serial
import fcntl
import time

if __name__ == '__main__':
  TIOCEXCL = 0x540C
  print('Running. Press ctrl-C to exit')
  arduino = serial.Serial(
      port="/dev/ttyUSB0", 
      timeout=1,
      baudrate=115200)
  # arduino = serial.Serial(
      # port="/dev/ttyUSB0", 
      # baudrate=115200,
      # parity=serial.PARITY_ODD, # Best setting
      # stopbits=serial.STOPBITS_TWO, # Best setting
      # bytesize=serial.SEVENBITS, # Best setting
      # timeout=None)
  arduino.flushInput()
  # fcntl.ioctl(arduino.fileno(), TIOCEXCL) # Exclusive
  time.sleep(0.2) # Wait for serial to open
  if not arduino.isOpen(): 
      print('Could not open port.')
      exit()
  print(f'{arduino.port} Connected!')
  try:
      while True:
        if arduino.in_waiting == 0: pass
        while arduino.in_waiting > 0:
#          print("In waiting before "+str(arduino.in_waiting))
          message = arduino.readline().decode('utf-8').strip()
#          print("In waiting after "+str(arduino.in_waiting))
          # arduino.flushInput()
          if message != '': print(message)
  except ValueError:
      print("Value error!")
      arduino.close()
  except serial.SerialException:
      print("Serial Exception!")
      arduino.close()
  except KeyboardInterrupt:
      print("Keyboard Interrupt")
      arduino.close()

# Author: Adrian Vrouwenvelder
def normalize_angle(angle):
    return angle % 360

# Return acute angle between two vectors. Always between -180 and 180, inclusive.
# 'actual' is measured from 'desired' so if actual > desired, this indicates actual lies to the right of desired.
# (i.e. the error is in the positive direction)
def calculate_angle_difference(desired, actual): # Positive means actual lies to right of desired. 
    angle = ( actual - desired + 180 ) % 360 - 180
    return (angle + 360) if angle < -180 else angle

def test_equals(expected, actual):
   if actual != expected: raise Exception(f"expected {expected} but got {actual}")

def celsius_to_fahrenheit(c):
   return c * 9 / 5 + 32

if __name__ == "__main__":
   test_equals(5, normalize_angle(365))
   test_equals(355, normalize_angle(-5))
   test_equals(0, normalize_angle(-360))
   test_equals(0, normalize_angle(360))
   test_equals(180, normalize_angle(180))
   test_equals(100, calculate_angle_difference(100,200)) 
   test_equals(-101, calculate_angle_difference(200,99)) 
   test_equals(-102, calculate_angle_difference(0,258)) 
   test_equals(110, calculate_angle_difference(260,10)) 
   test_equals(179, calculate_angle_difference(90,269)) # Interior angle includes bottom of circle
   test_equals(-179, calculate_angle_difference(90,271)) # Interior angle includes top of circle
   test_equals(179, calculate_angle_difference(271,90)) 
   test_equals(-179, calculate_angle_difference(269,90))
   test_equals(32, celsius_to_fahrenheit(0))
   test_equals(212, celsius_to_fahrenheit(100))

   print("All good!")


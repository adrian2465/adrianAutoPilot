# Author: Adrian Vrouwenvelder
def normalize_angle(angle):
    return angle % 360

def calculate_angle_difference(course, heading): # Too far to port means negative value
    angle = ( heading - course + 180 ) % 360 - 180
    return (angle + 360) if angle < -180 else angle

def test_equals(expected, actual):
   if actual != expected: raise Exception(f"expected {expected} but got {actual}")
   
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
   print("All good!")

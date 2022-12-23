## Adrian Vrouwenvelder
## December 1, 2022

def normalize(course:int) -> int:
    while (course >= 360): course = course - 360
    while (course < 0): course = course + 360
    return course

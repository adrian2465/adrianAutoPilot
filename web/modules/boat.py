from config import Config
from anglemath import normalize_angle

class Boat:

    def __init__(self):
        self._course = None
        self._rudder = 0
        self._commanded_rudder = None
        self._course_tolerance = 0.2

    @property
    def heading(self):
        """Boat's current heading."""
        return self._heading

    @heading.setter
    def heading(self, heading):
        self._heading = heading

    @property
    def course(self):
        """Desired course for aautopilot to steer"""
        return self._course

    @course.setter
    def course(self, course):
        self._course = course

    @property
    def rudder(self):
        """Returns normalized rudder (-1 for full port, 1 for full starboard, 0 for centered)"""
        return self._rudder

    @rudder.setter
    def rudder(self, rudder):
        self._rudder = rudder

    @property
    def is_on_course(self):
        return abs(self.course - self.heading) <= self._course_tolerance

    def rudder_as_string(self, rudder):
        """
        Boat rudder angle displayed as:
           '      ----      ' for centered rudder,
           '<==== 1.00      ' for hard over port rudder,
           '      1.00 ====>' for hard over starboard rudder
        Value displayed ranges from 0.01 to 1.00
        """
        rudder_tolerance = 0.01
        num_dashes = int(rudder * 4)
        blanks = ' ' * (4-num_dashes)
        dashes = '=' * num_dashes
        return   f"{blanks}<{dashes} {-rudder:1.2f}     " if rudder < -rudder_tolerance \
            else f"     {rudder:1.2f} {dashes}>{blanks}" if rudder > rudder_tolerance \
            else  "     ----      "

    @property
    def commanded_rudder(self):
        return self._commanded_rudder

    @commanded_rudder.setter
    def commanded_rudder(self, commanded_rudder):
        self._commanded_rudder = commanded_rudder

def rudder_as_string(rudder):
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


class Boat:

    def __init__(self):
        self._heading = None
        self._course = None
        self._commanded_rudder = None
        self._course_tolerance = 0.1

    @property
    def is_on_course(self):
        return abs(self._course - self._heading) <= self._course_tolerance

    @property
    def target_course(self):
        """Desired course for aautopilot to steer"""
        return self._course

    @target_course.setter
    def target_course(self, course):
        self._course = course

    @property
    def commanded_rudder(self):
        """Desired rudder angle. Range is 0 <= commanded_rudder <= 1"""
        return self._commanded_rudder

    @commanded_rudder.setter
    def commanded_rudder(self, commanded_rudder):
        self._commanded_rudder = commanded_rudder

    @property
    def heading(self):
        """Boat's current heading."""
        pass

    @property
    def heel(self):
        """Angle of heel in degrees. 0 = level"""
        pass


    @property
    def rudder(self):
        """Returns normalized rudder (-1 for full port, 1 for full starboard, 0 for centered)"""
        pass
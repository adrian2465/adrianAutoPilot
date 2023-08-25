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


class BoatInterface:

    def __init__(self, config):
        self._cfg = config.boat
        self._target_course = None
        self._commanded_rudder = None
        self._course_tolerance = self._cfg['course_tolerance_deg']
        self._rudder_hardover_time_s = self._cfg['rudder_hardover_time_s']
        self._max_boat_turn_rate_dps = self._cfg['boat_turn_rate_dps']
        self._rudder = None

    def get_target_course(self):
        """Desired course for aautopilot to steer"""
        return self._target_course

    def set_target_course(self, course):
        self._target_course = course

    def get_commanded_rudder(self):
        """Desired rudder angle. Range is 0 <= commanded_rudder <= 1"""
        return self._commanded_rudder

    def set_commanded_rudder(self, commanded_rudder):
        self._commanded_rudder = commanded_rudder

    def get_hard_over_time_s(self):
        return self._rudder_hardover_time_s

    def get_max_boat_turn_rate_dps(self):
        return self._max_boat_turn_rate_dps

    def is_on_course(self):
        return abs(self._target_course - self.get_heading()) <= self._course_tolerance

    def get_heading(self):
        """Boat's current heading."""
        pass

    def get_heel(self):
        """Angle of heel in degrees. 0 = level"""
        pass

    def get_rudder(self):
        """Returns normalized rudder (-1 for full port, 1 for full starboard, 0 for centered)"""
        pass

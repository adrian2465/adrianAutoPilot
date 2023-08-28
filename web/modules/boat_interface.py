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
        self._rudder = None

    def target_course(self):
        """Desired course for aautopilot to steer"""
        return self._target_course

    def set_target_course(self, course):
        self._target_course = course

    def commanded_rudder(self):  # TODO Commanded Rudder shouldn't really be part of boat, but should be part of brain.
        """Desired rudder angle. Range is 0 <= commanded_rudder <= 1"""
        return self._commanded_rudder

    def set_commanded_rudder(self, commanded_rudder):
        self._commanded_rudder = commanded_rudder

    def is_on_course(self):
        return abs(self._target_course - self.heading()) <= self._cfg['course_tolerance_deg']

    def hard_over_time_s(self):
        return self._cfg['rudder_hardover_time_s']

    def max_boat_turn_rate_dps(self):
        return self._cfg['boat_turn_rate_dps']

    def heading(self):
        """Boat's current heading."""
        pass

    def heel(self):
        """Angle of heel in degrees. 0 = level"""
        pass

    def rudder(self):
        """Returns normalized rudder (-1 for full port, 1 for full starboard, 0 for centered)"""
        pass


class BoatInterface:

    def __init__(self, cfg):
        self._cfg = cfg.boat
        self._rudder = None

    def hard_over_time_s(self):
        """Time from center to stop"""
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

    def __str__(self):
        """
        Boat rudder angle displayed as:
           '      ----      ' for centered rudder,
           '<==== 1.00      ' for hard over port rudder,
           '      1.00 ====>' for hard over starboard rudder
        Value displayed ranges from 0.01 to 1.00
        """
        rudder = self._rudder
        rudder_tolerance = 0.01
        num_dashes = int(abs(rudder * 4))
        blanks = ' ' * (4 - num_dashes)
        dashes = '=' * num_dashes
        return f"hdg={self.heading():5.1f} heel={self.heel():4.1f}" + \
            " rudder=" + \
               (f"{blanks}<{dashes} {-rudder:1.2f}     " if rudder < -rudder_tolerance \
                    else f"     {rudder:1.2f} {dashes}>{blanks}" if rudder > rudder_tolerance \
                   else "     ----      ")

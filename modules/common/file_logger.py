import datetime

from modules.common.config import Config


def timestamp():
    return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')


ERROR = 0
WARNING = 1
INFO = 2
DEBUG = 3
PI_CONSOLE = '/dev/tty0'


cfg = Config("configuration/config.yaml")


class Logger:

    def __init__(self, config_path, dest=None, who=None):
        component_config = cfg.boat if config_path == "boat" else \
            cfg.mpu if config_path == "mpu9250" else \
            cfg.pid if config_path == "pid" else \
            cfg.brain if config_path == "brain" else \
            cfg.arduino if config_path == "arduino" else \
            cfg.root

        if "log_level" in component_config:
            self._lvl = (component_config["log_level"])
        else:
            self._lvl = 2

        self._filedesc = None
        self._dest = dest
        self._who = who
        if dest is not None:
            if dest.startswith('/dev'):
                self._mode = 'w'
            else:
                self._mode = 'w+'

    def __del__(self):
        if self._filedesc is not None:
            self._filedesc.close()

    def _open(self):
        if self._filedesc is None:
            self._filedesc = open(self._dest, self._mode)

    def set_level(self, lvl):
        self._lvl = lvl

    def level(self):
        return self._lvl

    def write(self, msg):
        if self._dest is not None:
            self._open()
            self._filedesc.write(msg + '\n')
        else:
            print(msg)

    def write_with_level(self, lvl, msg):
        who_str = self._who if self._who is not None else "?????"
        if lvl <= self._lvl:
            lvl_msg = "DEBUG" if lvl == DEBUG \
                else "INFO " if lvl == INFO  \
                else "WARN " if lvl == WARNING  \
                else "ERROR" if lvl == ERROR \
                else "UNKWN"
            self.write(f'{timestamp()} - {lvl_msg} - {who_str}: {msg}')

    def info(self, msg):
        self.write_with_level(INFO, msg)

    def debug(self, msg):
        self.write_with_level(DEBUG, msg)

    def warn(self, msg):
        self.write_with_level(WARNING, msg)

    def error(self, msg):
        self.write_with_level(ERROR, msg)
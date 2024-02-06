# Author: Adrian Vrouwenvelder
# April 9, 2023
import os
from pathlib import Path

import yaml
import threading
import logging
import logging.config
from modules.common.test_methods import test_equals

CONFIG_DIR_NAME='configuration'
LOGGING_CONF_FILE_NAME= "logging.conf"
DEFAULT_CONFIG_FILE = "config.yaml"
OVERRIDE_CONFIG_FILE = "config_overrides.yaml"
CONFIG_FILE_TEST_PREFIX="test_"

class Config:
    _data_lock = threading.Lock()
    _defaults_dict = None
    _overrides_dict = None
    _combined_dict = None
    _defaults_file = None
    _overrides_file = None
    _config_dir = None
    _logger = None

    usb_device = "/dev/ttyUSB0"
    usb_baud_rate = 115200

    @staticmethod
    def init(is_test=False):
        if Config._combined_dict is None:
            Config._config_dir = Path("configuration")
            log_conf_file = Path(Config._config_dir, LOGGING_CONF_FILE_NAME)
            logging.config.fileConfig(log_conf_file)
            Config._logger = logging.getLogger("config")
            logger = Config._logger
            logger.debug(f"Using logging configuration file {os.path.normpath(log_conf_file.absolute())}")
            default_file_name = DEFAULT_CONFIG_FILE if not is_test else CONFIG_FILE_TEST_PREFIX + DEFAULT_CONFIG_FILE
            overrides_file_name = OVERRIDE_CONFIG_FILE if not is_test else CONFIG_FILE_TEST_PREFIX + OVERRIDE_CONFIG_FILE
            defaults_config_file = Path(Config._config_dir, default_file_name)
            if not defaults_config_file.exists():
                raise Exception(f"{os.path.normpath(defaults_config_file.absolute())} does not exist")
            Config._defaults_file = defaults_config_file
            Config._overrides_file = Path(Config._config_dir, overrides_file_name)
            logger.debug(f"Using defaults file {os.path.normpath(Config._defaults_file.absolute())}")
            if Config._defaults_file is None or Config._overrides_file is None:
                raise Exception("Program error. Config is not initialized")
            with Config._data_lock:
                if Config._combined_dict is None:
                    with open(Config._defaults_file, 'r') as stream:
                        logger.debug(f"Loading defaults file: {os.path.normpath(Config._defaults_file.absolute())}")
                        Config._defaults_dict = yaml.safe_load(stream)
                if Config._overrides_dict is None:
                    if Config._overrides_file.is_file():
                        with open(Config._overrides_file, 'r') as stream:
                            logger.debug(f"Loading overrides file: {os.path.normpath(Config._overrides_file.absolute())}")
                            Config._overrides_dict = yaml.safe_load(stream)
                    else:
                        Config._overrides_dict = {}
                Config._combined_dict = Config._defaults_dict | Config._overrides_dict

    @staticmethod
    def get_or_else(val_name, default):
        return Config._combined_dict[val_name] if val_name in Config._combined_dict else default

    @staticmethod
    def get(val_name):
        return Config._combined_dict[val_name]

    @staticmethod
    def save(val_name, value):
        Config._overrides_dict[val_name] = value
        Config._combined_dict = Config._defaults_dict | Config._overrides_dict

        with open(Config._overrides_file, 'w') as f:
            yaml.dump(Config._overrides_dict, f, default_flow_style=False)

if __name__ == "__main__":
    test_config_line = "overridden_value: 'INITIAL_OVERRIDE_VALUE'"
    with open("configuration/test_config_overrides.yaml", 'w') as stream:
        print(test_config_line, file=stream)
    Config.init(True)

    logger = logging.getLogger("config_test")
    logger.info(f"Testing {Config.__name__}")
    # # TEST CONFIGURATION
    # test_value: 100
    # test_array: [10, 20]
    # nested_config:
    #   config1: 'A'
    #   config2: 'B'
    test_equals(100, Config.get('test_value'))
    test_equals([10, 20], Config.get('test_array'))
    test_equals('A', Config.get('nested_config')['config1'])
    test_equals('B', Config.get('nested_config')['config2'])
    test_equals(100, Config.get('test_value'))
    test_equals(228, int(Config.get('rudder_port_limit')))
    test_equals(701, int(Config.get('rudder_starboard_limit')))
    test_equals("INITIAL_OVERRIDE_VALUE", Config.get('overridden_value'))
    Config.save('overridden_value', 'OK')
    with open(Config._overrides_file, 'r') as stream:
        l = stream.readline().strip()
        if l != "overridden_value: OK": raise Exception(f"Unexpected contents of {Config._overrides_file} = {l}")
    try:
        test_equals(100, Config.get('bogus'))
        raise Exception("found 'bogus' but should not have")
    except KeyError as e:
        pass
    test_equals(100, Config.get_or_else('bogus', 100))
    test_equals(100, Config.get_or_else('test_value', 0))

    logger.info("All tests passed")

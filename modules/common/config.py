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

class Config:
    _data_lock = threading.Lock()
    _config_dict = None
    _config_file = None
    _config_dir = None
    _logger = None

    @staticmethod
    def init(file_name):
        if Config._config_file is None:
            Config._config_dir = Path("configuration")
            log_conf_file = Path(Config._config_dir, LOGGING_CONF_FILE_NAME)
            logging.config.fileConfig(log_conf_file)
            Config._logger = logging.getLogger("config")
            logger = Config._logger
            logger.debug(f"Using logging configuration file {os.path.normpath(log_conf_file.absolute())}")
            config_file = Path(Config._config_dir, file_name)
            if not config_file.exists(): raise Exception(f"{os.path.normpath(config_file.absolute())} does not exist")
            Config._config_file = config_file
            logger.debug(f"Using configuation file {os.path.normpath(Config._config_file.absolute())}")

    @staticmethod
    def getConfig():
        logger = Config._logger
        if Config._config_dict is None:
            if Config._config_file is None: raise Exception("Config is not initialized")
            with Config._data_lock:
                if Config._config_dict is None:
                    with open(Config._config_file, 'r') as stream:
                        logger.debug(f"Loading configuration file: {os.path.normpath(Config._config_file.absolute())}")
                        Config._config_dict = yaml.safe_load(stream)
        return Config._config_dict

    @staticmethod
    def get(val_name, default=None):
        config = Config.getConfig()
        if val_name in config:
            return config[val_name]
        elif default is None:
            raise KeyError(f"'{val_name}' not found in config")
        else:
            return default


if __name__ == "__main__":
    Config.init("test_config.yaml")
    logger = logging.getLogger("config_test")
    logger.info(f"Testing {Config.__name__}")
    cfg = Config.getConfig()
    # # TEST CONFIGURATION
    # test_value: 100
    # test_array: [10, 20]
    # nested_config:
    #   config1: 'A'
    #   config2: 'B'
    test_equals(100, cfg['test_value'])
    test_equals([10, 20], cfg['test_array'])
    test_equals('A', cfg['nested_config']['config1'])
    test_equals('B', cfg['nested_config']['config2'])
    test_equals(100, Config.get('test_value'))
    try:
        test_equals(100, Config.get('bogus'))
        raise Exception("found 'bogus' but should not have")
    except KeyError as e:
        pass
    test_equals(100, Config.get('bogus', 100))
    test_equals(100, Config.get('test_value', 0))
    logger.info("All tests passed ONLY IF this is the last message!")
    Config.init("../../configuration/test_config.yaml")  # Should be no-op
    Config.getConfig()  # Should be no-op

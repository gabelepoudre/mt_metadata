# -*- coding: utf-8 -*-
"""
Root logging

Created on Mon May 18 15:34:05 2020

@author: jpeacock
"""

import logging
import logging.config
from pathlib import Path
import yaml

FORMATTER = logging.Formatter("%(asctime)s [line %(lineno)d] %(name)s.%(funcName)s - %(levelname)s: %(message)s")
CONF_PATH = Path(__file__).parent
CONF_FILE = Path.joinpath(CONF_PATH, "logging_config.yaml")
LOG_PATH = CONF_PATH.parent.parent.joinpath("logs")
LEVEL_DICT = {"debug": logging.DEBUG,
              "info": logging.INFO,
              "warning": logging.WARNING,
              "error": logging.ERROR,
              "critical": logging.CRITICAL}

if not CONF_PATH.exists():
    CONF_PATH.mkdir()

if not CONF_FILE.exists():
    CONF_FILE = None

def load_logging_config(config_fn=CONF_FILE):
    """
    Load logging configuration file
    """
    config_file = Path(config_fn)
    with open(config_file, "r") as fid:
        config_dict = yaml.safe_load(fid)
    logging.config.dictConfig(config_dict)

def get_logger(logger_name, fn=None, level="debug"):
    """
    Create a logger, can write to a separate file.  This will write to
    the logs folder in the mt_metadata directory.
    
    :param logger_name: name of the logger, typically __name__
    :type logger_name: string
    :param fn: file name to write to, defaults to None
    :type fn: TYPE, optional
    :param level: DESCRIPTION, defaults to "debug"
    :type level: TYPE, optional
    :return: DESCRIPTION
    :rtype: TYPE

    """
    logger = logging.getLogger(logger_name)
    if fn is not None:
        fn = LOG_PATH.joinpath(fn)
        exists = False
        if fn.exists():
            exists = True
        if fn.suffix not in [".log"]:
            fn = Path(fn.parent, f"{fn.stem}.log")
        fn_handler = logging.handlers.RotatingFileHandler(fn,
                                                          mode="a",
                                                          maxBytes=2485760, 
                                                          backupCount=2)
        fn_handler.setFormatter(FORMATTER)
        fn_handler.setLevel(LEVEL_DICT[level.lower()])
        logger.addHandler(fn_handler)
        if not exists:
            logger.info(f"Logging file can be found {logger.handlers[-1].baseFilename}")
    else:
        logger.addHandler(logging.NullHandler())

    return logger
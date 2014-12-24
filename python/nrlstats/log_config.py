"""
Imports logging configuration from the config file
"""

import logging.config
import os.path
LOGGING_CONF=os.path.join(os.path.dirname(__file__), "log_config.ini")

logging.config.fileConfig(LOGGING_CONF)
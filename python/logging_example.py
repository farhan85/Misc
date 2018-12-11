#!/usr/bin/env python

import codecs
import logging
import logging.config
import time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler


FILENAME = 'application.log'


class UTCFormatter(logging.Formatter):
    """A logging formatter where all timestamps are logged in UTC time"""

    converter = time.gmtime


class CurrentFileWithTimestampHandler(TimedRotatingFileHandler):
    """
    Extends the ``TimedRotatingFileHandler`` class to generate log files where
    all files (including the current) has a timestamp in the filename.

    The current log file will always have the current timestamp in the filename,
    and the format of the timestamp will be using Timber's required format.
    """

    def __init__(self, filename, when='H', interval=1, backupCount=0,
                 encoding='utf-8', delay=False, utc=True):

        if when == 'S':
            suffix = '%Y-%m-%d-%H-%M-%S'
        if when == 'M':
            suffix = '%Y-%m-%d-%H-%M'
        if when == 'H':
            suffix = '%Y-%m-%d-%H'
        if when == 'D':
            suffix = '%Y-%m-%d'

        self._base_filename = filename
        self._suffix = suffix

        filename = self.gen_filename()
        TimedRotatingFileHandler.__init__(self, filename, when, interval,
                backupCount, encoding, delay, utc)

    def gen_filename(self):
        return '{}.{}'.format(self._base_filename,
                              datetime.utcnow().strftime(self._suffix))

    def doRollover(self):
        self.stream.close()
        filename = self.gen_filename()
        self.stream = codecs.open(filename, 'w', encoding=self.encoding)
        self.rolloverAt = self.rolloverAt + self.interval


logging_config = {
    'version': 1,
    'formatters': {
        'default_formatter': {
            'format': '%(asctime)s.%(msecs)03d %(levelname)-8s %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            '()': UTCFormatter
            }
        },
    'handlers': {
        # Note the initial file is created in the constructor, so only
        # use one file handler in production
        'file_handler_1': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'default_formatter',
            'filename': FILENAME,
            'when': 'H',
            'interval': 1,
            'level': logging.DEBUG
            },
        'file_handler_2': {
            'class': '__main__.CurrentFileWithTimestampHandler',
            'formatter': 'default_formatter',
            'filename': FILENAME,
            'when': 'H',
            'interval': 1,
            'level': logging.DEBUG
            },
        'console_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'default_formatter',
            'level': logging.DEBUG
            }
        },
    'root': {
        'handlers': ['file_handler_1', 'console_handler'],
        'level': logging.DEBUG
        }
    }


logging.config.dictConfig(logging_config)
log = logging.getLogger(__name__)


log.critical('test')
log.error('test')
log.warning('test')
log.info('test')
log.debug('test')

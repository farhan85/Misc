# For when python applications are run as short-running jobs (controlled by cron)
# this script allows us to manually rotate the log files (if a TimedRotatingFileHandler
# was already configured).
#
# Just add this job to the list of cronjobs
# You'll need to have already configured the loggers before using this module

import json
import logging
import logging.config
from logging.handlers import BaseRotatingHandler


def rotate_logs():
    handlers = set([])
    root = logging.getLogger()

    # Process root logger as well
    loggers = [root]
    loggers.extend(root.manager.loggerDict.itervalues())

    for logger in loggers:
        try:
            for handler in logger.handlers:
                if (isinstance(handler, BaseRotatingHandler) and handler not in handlers):
                    handlers.add(handler)

        except AttributeError:
            pass

    for h in handlers:
        h.doRollover()

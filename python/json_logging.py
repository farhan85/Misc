#!/usr/bin/env python3

import logging
from pythonjsonlogger import jsonlogger


logger = logging.getLogger()

logger.setLevel(logging.INFO)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('''%(asctime)s, %(process)s, %(name)s, %(levelname)s,
        %(pathname)s, %(funcName)s, %(message)s, %(lineno)s''')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

logger.info('foo')
logger.error('bar', extra={'id': 'helloworld'})

#!/usr/bin/env python3

import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


if __name__ == '__main__':
    log = logging.getLogger()
    log.debug('Debug log')
    log.info('Info log')
    log.warning('Warning log')
    log.error('Error log')
    log.critical('Critial log')
    try:
        raise Exception('Test exception')
    except:
        log.exception('Exception log')

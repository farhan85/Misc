#!/usr/bin/env python3

import logging
import sys


def run_test_1():
    log = logging.getLogger(__name__)
    log.info('Another info log')
    log.debug('Debug log')
    log.info('Info log')
    log.warning('Warning log')
    log.error('Error log')
    log.critical('Critial log')
    try:
        raise Exception('Test exception')
    except:
        log.exception('Exception log')


def run_test_2():
    logging.debug('Debug log')
    logging.info('Info log')
    logging.warning('Warning log')
    logging.error('Error log')
    logging.critical('Critial log')
    try:
        raise Exception('Test exception')
    except:
        logging.exception('Exception log')


if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stdout,
        format='%(asctime)s %(name)s:%(module)s %(levelname)s %(message)s')
    run_test_1()

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format='%(asctime)s %(name)s:%(module)s %(levelname)s %(message)s',
        force = True)
    run_test_2()

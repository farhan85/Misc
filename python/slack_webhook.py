#!/usr/bin/env python3

import click
import http.client as http_client
import logging
import requests
import sys


WEBHOOK_URL = '...'


def setup_logger():
    # Enable debugging at httplib level (requests->urllib3->http.client)
    # This will log headers and data, and response headers (without data)
    http_client.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def send_message(message):
    json_data = { 'content': message }
    response = requests.post(WEBHOOK_URL, json=json_data)
    print('Message sent. Response: {} {}'.format(response.getcode(), response.reason))


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-v', '--verbose', is_flag=True, help='Enable debug logging')
@click.argument('message', required=False)
def main(verbose, message):
    if verbose:
        setup_logger()

    # Allow messages to also be piped into this script
    if not message and not sys.stdin.isatty():
        message = sys.stdin.read()

    if not message:
        raise ValueError('No message given')

    send_message(message)


if __name__ == '__main__':
    main()

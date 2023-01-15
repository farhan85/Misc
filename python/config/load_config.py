#!/usr/bin/env python3

from configparser import ConfigParser, ExtendedInterpolation


def load_config(stage):
    parser = ConfigParser(defaults={'stage': stage},
                          interpolation=ExtendedInterpolation())
    with open('config.ini') as f:
        parser.read_file(f)
    return parser[stage]


for cfg in (load_config('local'), load_config('test'), load_config('prod')):
    print('Application:', cfg['application_name'])
    print('Table:', cfg['users_table_name'])
    print('Max retries:', cfg['max_retries'])
    print('Connection URL:', cfg['connection_url'])
    print()

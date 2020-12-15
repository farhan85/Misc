#!/usr/bin/env python3

from configparser import ConfigParser, ExtendedInterpolation


def load_config(stage):
    parser = ConfigParser(
            defaults={'stage': stage},
            interpolation=ExtendedInterpolation())
    with open('config.ini') as f:
        parser.read_file(f)
    return parser[stage]


cfg = load_config('local')
print(cfg['application_name'])
print(cfg['users_table_name'])
print(cfg['max_retry_time_s'])
print(cfg['connection_url'])
print()

cfg = load_config('test')
print(cfg['application_name'])
print(cfg['users_table_name'])
print(cfg['max_retry_time_s'])
print(cfg['connection_url'])
print()

cfg = load_config('prod')
print(cfg['application_name'])
print(cfg['users_table_name'])
print(cfg['max_retry_time_s'])
print(cfg['connection_url'])

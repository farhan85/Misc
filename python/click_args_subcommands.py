#!/usr/bin/env python3
"""
Main program doc (not used in --help output).
"""

import click


CLICK_CONTEXT_SETTINGS = {'help_option_names': ['-h', '--help']}


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def cli():
    pass

@cli.command(context_settings=CLICK_CONTEXT_SETTINGS)
@click.option('-n', '--name', help='Argument with string value', default='Joe', show_default=True)
@click.option('--flag-a', is_flag=True)
def foo(name, flag_a):
    """Program definition"""

    print("Name:", name)
    print("Flag A:", flag_a)

@cli.command(context_settings=CLICK_CONTEXT_SETTINGS)
@click.option('-c', '--count', help='Forcing a number format', type=int)
@click.option('--flag-b/--no-flag-b', help='Another way of specifying a flag', default=False, show_default=True)
def bar(count, flag_b):
    """Program definition"""

    print("Count:", count)
    print("Flag B:", flag_b)


if __name__ == '__main__':
    cli()

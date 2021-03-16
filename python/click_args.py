#!/usr/bin/env python3
"""
Main program doc (not used in --help output).
"""

# Alternatively, instad of defining the show_default parameter for every option,
# you can use a partial:
#
#   import functools
#
#   # Use this instead of click.option
#   click_option = functools.partial(click.option, show_default=True)
#
#   @click.command()
#   @click_option('-c', '--count')
#   def main(count):
#       pass

import click


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-n', '--name', help='Argument with string value', default='Joe', show_default=True)
@click.option('-c', '--count', help='Forcing a number format', type=int)
@click.option('--flag-a', is_flag=True, help='Example of a flag')
@click.option('--flag-b/--no-flag-b', help='Another way of specifying a flag', default=False, show_default=True)
def main(name, count, flag_a, flag_b):
    """Program definition"""

    print("Name:", name)
    print("Count:", count)
    print("Flag A:", flag_a)
    print("Flag B:", flag_b)


if __name__ == '__main__':
    main()

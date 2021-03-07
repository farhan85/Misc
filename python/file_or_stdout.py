"""
As example of using a context manager to write to a file or stdout
This is most useful with program args for specifying writing output
to a file, or stdout by default. For example::

    @click.option('-o', '--output', help='Output filename (stdout if not specified)')
    def main(output):
        with file_writer(output) as f:
            print_something(f)
"""

import contextlib
import sys


@contextlib.contextmanager
def file_writer(filename=None):
    # Create writer object based on file name
    writer = open(filename, 'w') if filename else sys.stdout
    # yield the writer object for the actual use
    yield writer
    # If we did open a file, then close the writer object
    if filename: writer.close()


if __name__ == '__main__':
    with file_writer('output.txt') as f:
        f.write("Hello world. I've written to a file\n")

    with file_writer() as f:
        f.write("Hello world. I've written to stdout\n")

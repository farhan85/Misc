#!/usr/bin/env python

import argparse
import os
import sys
import pymupdf


USAGE = '''
Examples:
  ./%(prog)s doc1.pdf doc2.pdf doc3.pdf merged_output.pdf
'''


def combine_pdfs(input_filenames, output_filename):
    output_path = os.path.realpath(output_file)
    with pymupdf.open() as new_pdf:
        for fname in input_filenames:
            if output_path == os.path.realpath(fname):
                raise ValueError('Output file cannot be any of the input files')
            if not os.path.exists(fname):
                print(f'File '{fname}' not found. Skipping file')

            with pymupdf.open(fname) as input_pdf:
                new_pdf.insert_pdf(input_pdf)

        new_pdf.save(output_filename)
        print(f'Created {output_filename}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Combine multiple PDF files into one',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=USAGE
    )
    parser.add_argument('inputs', nargs='+', help='Input PDF files in order')
    parser.add_argument('output', help='Output combined PDF file')
    args = parser.parse_args()

    try:
        combine_pdfs(args.inputs, args.output)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


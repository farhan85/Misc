#!/usr/bin/env python

import argparse
import os
import sys
import pymupdf


USAGE = '''
Examples:
  ./%(prog)s -p 1 3 16 -f input.pdf -o output.pdf
'''


def main(input_filename, output_filename, page_numbers):
    if os.path.realpath(input_filename) == os.path.realpath(output_filename):
        raise ValueError('Input and output files must be different')

    # Remove duplicates, otherwise we would end up deleting consecutive pages
    page_numbers = set(page_numbers)
    # Remove pages in descending order, otherwise deleting earlier pages causes
    # the page numbering to shift and we'll delete the wrong pages later on
    pages_to_delete = sorted(page_numbers, reverse=True)

    with pymupdf.open(input_filename) as input_pdf:
        for page_num in pages_to_delete:
            if 0 <= page_num < len(input_pdf):
                input_pdf.delete_page(page_num)
            else:
                print(f'Page {page_num} is out of bounds. Skipping page')

        input_pdf.save(output_filename)
        print(f'Updated {output_filename}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Remove specific pages from a PDF file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=USAGE
    )
    parser.add_argument('-f', '--file', dest='input', help='Path to the input PDF file')
    parser.add_argument('-o', '--output', help='Path to save the output PDF file')
    parser.add_argument('-p', '--pages', nargs='+', type=int, required=True,
        help='Space-separated list of page numbers to remove')
    args = parser.parse_args()

    try:
        pages = [p - 1 for p in args.pages]  # Convert to 0-indexed numbers
        main(args.input, args.output, pages)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


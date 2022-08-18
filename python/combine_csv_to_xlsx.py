#!/usr/bin/env python

import csv
import glob
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell


# Note this assumes each csv file has the same format:
#  - The first row is the header
#  - The first column are string values (identifiers)
#  - All other cells are integer values

with xlsxwriter.Workbook('combined.xlsx') as workbook:
    for filename in glob.glob('*.csv'):
        # Note: worksheet names cannot exceed 31 characters
        worksheet_name = filename.replace('.csv', '')
        worksheet = workbook.add_worksheet(worksheet_name)

        with open(filename) as f:
            reader = csv.reader(f)
            for r, row in enumerate(reader):
                for c, col in enumerate(row):
                    if r == 0 or c == 0:
                        worksheet.write(r, c, col)
                    else:
                        worksheet.write(r, c, int(col))

            first_col_start = xl_rowcol_to_cell(1, 0)
            first_col_end = xl_rowcol_to_cell(r, 0)
            worksheet.ignore_errors({'number_stored_as_text': f'{first_col_start}:{first_col_end}'})


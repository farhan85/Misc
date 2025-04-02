#!/usr/bin/env python
"""
Creates a custom calendar in PDF format.
"""

import calendar
import contextlib
import errno
import shutil
import tempfile
from calendar import Calendar
from collections import defaultdict
from datetime import date, datetime, timedelta

import click
import configparser
import pdfkit
import yaml
from enum import Enum
from jinja2 import Environment, FileSystemLoader, select_autoescape


CLICK_CONTEXT_SETTINGS = {'help_option_names': ['-h', '--help']}


@contextlib.contextmanager
def temp_directory():
    name = tempfile.mkdtemp()
    try:
        yield name
    finally:
        try:
            shutil.rmtree(name)
        except OSError as e:
            # Reraise if not ENOENT (no such file or directory).
            # It's okay if the directory has already been deleted.
            if e.errno != errno.ENOENT:
                raise


def date_range(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield start_date + timedelta(n)


class DayType(Enum):
    """ Represents a type of day """

    NORMAL = 1
    SCHOOL_HOLIDAY = 2
    PUBLIC_HOLIDAY = 3

    def __lt__(self, other):
        if self.__class__ != other.__class__:
            return NotImplemented
        return self.value < other.value

    def __gt__(self, other):
        if self.__class__ != other.__class__:
            return NotImplemented
        return self.value > other.value

    @classmethod
    def from_str(cls, s):
        if s.lower() == 'public holiday':
            return cls.PUBLIC_HOLIDAY
        elif s.lower() == 'school holiday':
            return cls.SCHOOL_HOLIDAY
        else:
            return cls.NORMAL


class Cell(object):
    """ Represents a cell in the monthly calendar """

    def __init__(self, day_num=None):
        self.day_num = day_num
        self.day_type = DayType.NORMAL
        self.notes = []

    @property
    def day(self):
        return str(self.day_num) if self.day_num is not None else ''

    def _add_notes(self, notes):
        if isinstance(notes, list):
            self.notes.extend(notes)
        else:
            self.notes.append(notes)

    def _update_day_type(self, day_type):
        if day_type > self.day_type:
            self.day_type = day_type

    def update(self, day_type=None, notes=None):
        if day_type:
            self._update_day_type(day_type)
        if notes:
            self._add_notes(notes)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return '{}({}, {}, {})'.format(self.__class__.__name__, self.day_num,
            str(self.day_type), repr(self.notes))


class CalendarInfo(object):
    def __init__(self):
        self.days = defaultdict(dict)

    def for_day(self, month, day):
        if day not in self.days[month]:
            self.days[month][day] = Cell(day)
        return self.days[month][day]

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return str(self.days)


def to_date(s, year):
    """Converts string in 'DD MMM' format (eg 1 Feb) to a date object. """

    try:
        return datetime.strptime(s, '%d %b').replace(year=year).date()
    except ValueError:
        return datetime.strptime(s, '%d %B').replace(year=year).date()


def load_calendar_info(config):
    calendar_info = CalendarInfo()
    year = int(config['MAIN']['year'])

    for _, holiday_range in config['SCHOOL HOLIDAYS'].iteritems():
        start_date, end_date = (d.strip() for d in holiday_range.split('-'))
        start_date, end_date = to_date(start_date, year), to_date(end_date, year)
        for d in date_range(start_date, end_date):
            calendar_info.for_day(d.month, d.day).update(day_type=DayType.SCHOOL_HOLIDAY)

    for dt, note in config['PUBLIC HOLIDAYS'].iteritems():
        dt = to_date(dt, year)
        calendar_info.for_day(dt.month, dt.day).update(DayType.PUBLIC_HOLIDAY, note)

    for dt, note in config['MISC DAYS'].iteritems():
        dt = to_date(dt, year)
        note = [n.strip() for n in note.split(',')]
        calendar_info.for_day(dt.month, dt.day).update(notes=note)

    return calendar_info


class MonthConfig(object):
    """ The month being rendered into a page of a monthly calendar """

    def __init__(self, year, month, calendar_info):
        self.month = month
        self.calendar_info = calendar_info
        self.first_day = date(year, month, 1)
        self.name = self.first_day.strftime('%B')
        _days = Calendar(firstweekday=6).monthdayscalendar(year, month)
        if len(_days) == 6:
            first_row = self.merge_lists(_days[0], _days[-1])
            _days = [first_row] + _days[1:-1]
        self.days = _days

    @staticmethod
    def merge_lists(lst1, lst2):
        return [x if x != 0 else y for x, y in zip(lst1, lst2)]

    def num_rows(self):
        return len(self.days)

    def cell(self, row, col):
        day = self.days[row][col]
        if day == 0:
            return Cell()
        else:
            return self.calendar_info.for_day(self.month, day)


def month_template():
    """ Returns the template to use to create a page of the monthly calendar """

    loader = FileSystemLoader('.')
    env = Environment(loader=loader, autoescape=select_autoescape(['html']))
    return env.get_template('month.html.j2')


def rotate(lst, pos=1):
    if pos == 0 or len(lst) == 0:
        return lst

    pos = pos % len(lst)
    return lst[pos:] + lst[:pos]


def create_month_page(template, year, month_config):
    """ Creates a page of the monthly calendar for the given year and month """

    day_names = rotate(list(calendar.day_name), -1)
    return template.render(year=year, month=month_config, days=day_names)


def create_calendar(template, year, month_configs, output_filename):
    """ Creates the pdf monthly calendar """

    pdf_options = {
        'orientation': 'Landscape',
        'title' : 'Calendar {}'.format(year),
        'page-size': 'A4',
        'zoom': 18,
    }

    with temp_directory() as dirname:
        files_months = []
        for month_config in month_configs:
            fd, tmp_path = tempfile.mkstemp(dir=dirname, suffix='.html')
            files_months.append(tmp_path)
            with open(tmp_path, 'w') as f:
                f.write(create_month_page(template, year, month_config))

        pdfkit.from_file(files_months, output_filename, options=pdf_options)


@click.command(context_settings=CLICK_CONTEXT_SETTINGS)
@click.option('-f', '--config-file', default='./dates.ini', help='Config file')
def main(config_file):
    print 'Reading config from {}'.format(config_file)
    conf = configparser.ConfigParser()
    conf.read(config_file)

    print 'Loading...'
    year = int(conf['MAIN']['year'])
    calendar_info = load_calendar_info(conf)

    month_configs = [MonthConfig(year, m, calendar_info) for m in range(1, 13)]
    template = month_template()

    print 'Generating calendar for year {}'.format(year)
    fname = 'calendar_{}.pdf'.format(year)

    create_calendar(template, year, month_configs, fname)
    print 'Calendar saved at {}'.format(fname)
    pass


if __name__ == '__main__':
    main()

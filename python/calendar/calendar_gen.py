import configparser
from calendar import Calendar
from datetime import date, datetime, timedelta
from enum import Enum

import click
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS


HTML_TEMPLATE = 'calendar.html.j2'
CSS_FILE = 'calendar.css'
DAY_NAMES = ('Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
MAX_CALENDAR_WEEKS = 6


class DayType(Enum):
    """ Represents a type of day """

    NORMAL = 1
    SCHOOL_HOLIDAY = 2
    PUBLIC_HOLIDAY = 3

    def __lt__(self, other):
        return self.value < other.value

    def __gt__(self, other):
        return self.value > other.value

    @classmethod
    def from_str(cls, s):
        if s.lower() == 'public holiday':
            return cls.PUBLIC_HOLIDAY
        elif s.lower() == 'school holiday':
            return cls.SCHOOL_HOLIDAY
        else:
            return cls.NORMAL


class Cell:
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


class CalendarInfo(object):
    def __init__(self):
        self.days = {}

    def for_day(self, month, day):
        d_month = self.days.setdefault(month, {})
        return d_month.setdefault(day, Cell(day))

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return str(self.days)


class MonthConfig(object):
    """ The month being rendered into the jinja page of a monthly calendar """

    def __init__(self, year, month, calendar_info):
        self.month = month
        self.calendar_info = calendar_info
        self.first_day = date(year, month, 1)
        self.name = self.first_day.strftime('%B')
        _days = Calendar(firstweekday=6).monthdayscalendar(year, month)
        if len(_days) == MAX_CALENDAR_WEEKS:
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


def date_range(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield start_date + timedelta(n)


def to_date(s, year):
    """Converts string in 'DD MMM' format (eg 1 Feb) to a date object. """
    return datetime.strptime(f'{s} {year}', '%d %b %Y').date()


def load_calendar_info(config):
    calendar_info = CalendarInfo()
    year = int(config['MAIN']['year'])
    for holiday_range in config['SCHOOL HOLIDAYS'].values():
        s_start_date, s_end_date = (d.strip() for d in holiday_range.split('-'))
        start_date, end_date = to_date(s_start_date, year), to_date(s_end_date, year)
        for d in date_range(start_date, end_date):
            calendar_info.for_day(d.month, d.day).update(day_type=DayType.SCHOOL_HOLIDAY)
    for dt, note in config['PUBLIC HOLIDAYS'].items():
        dt = to_date(dt, year)
        calendar_info.for_day(dt.month, dt.day).update(DayType.PUBLIC_HOLIDAY, note)
    for dt, note in config['MISC DAYS'].items():
        dt = to_date(dt, year)
        note = [n.strip() for n in note.split(',')]
        calendar_info.for_day(dt.month, dt.day).update(notes=note)
    return calendar_info


def calendar_template():
    """ returns the template to use to create the calendar """
    loader = FileSystemLoader('.')
    env = Environment(loader=loader, autoescape=select_autoescape(['html']))
    return env.get_template(HTML_TEMPLATE)


def rotate(lst, pos):
    if pos <= 0 or pos >= len(lst):
        return lst
    return lst[pos:] + lst[:pos]


def render_month_page(template, year, month_config):
    return template.render(year=year, month=month_config, days=DAY_NAMES)


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-f', '--config-file', default='./dates.ini', help='Config file')
def main(config_file):
    print('Reading config from {}'.format(config_file))
    conf = configparser.ConfigParser()
    conf.read(config_file)

    print('Loading...')
    year = int(conf['MAIN']['year'])
    fname = f'calendar_{year}.pdf'
    calendar_info = load_calendar_info(conf)
    template = calendar_template()
    month_configs = [MonthConfig(year, m, calendar_info) for m in range(1, 13)]
    html_str =  template.render(year=year, months=month_configs, days=DAY_NAMES)
    html = HTML(string=html_str)
    html.write_pdf(fname, stylesheets=[CSS(filename=CSS_FILE)])
    print(f'Calendar saved at {fname}')


if __name__ == '__main__':
    main()

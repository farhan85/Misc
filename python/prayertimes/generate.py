import argparse
import calendar
import json
import os
import requests
import weasyprint
from collections import namedtuple
from datetime import datetime
from jinja2 import Template


Location = namedtuple('Location', 'short long')

MONTHS = list(calendar.month_name)[1:]
PRAYER_TIMES_TEMPLATE = 'template.html.jinja'
LOCATIONS = [
    Location('Newcastle', 'Newcastle, NSW, Australia'),
    Location('Seattle', 'Seattle, WA, USA'),
]


def get_location(loc_str):
    # Use prefix search so we don't have to type the whole location name
    loc_str = loc_str.lower()
    for loc in LOCATIONS:
        if loc[0].lower().startswith(loc_str):
            return loc
    raise RuntimeError(f'Could not find location for {loc_str}')


def prayer_times_data(year, location):
    # https://aladhan.com/prayer-times-api#tag/annual-prayer-times-calendar/GET/calendarByAddress/{year}
    # Method 3 = Muslim World League
    api_url = f'https://api.aladhan.com/v1/calendarByAddress/{year}'
    params = {'address': location.long, 'method': 3}
    print(f'Retrieving data from {api_url}')
    response = requests.get(api_url, params=params)
    response.raise_for_status()
    return  response.json()['data']


def load_prayer_times_data(year, location):
    cache_filename = f'data_{location.short}_{year}.json'.lower()
    if os.path.exists(cache_filename):
        print(f'Reading cached data from {cache_filename}')
        with open(cache_filename, 'r', encoding='utf-8') as f:
            return json.load(f)

    raw_data = prayer_times_data(year, location)
    with open(cache_filename, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, indent=2)
    print(f'Saved data to {cache_filename}')
    return raw_data


def format_time(time_str):
    dt = datetime.strptime(time_str.split(' ')[0], '%H:%M')
    return dt.strftime('%-I:%M %p').lower()


def to_monthly_data(raw_data):
    monthly_data = []
    for m_idx in range(1, 13):
        daily_data = []
        for day_entry in raw_data[str(m_idx)]:
            day_name = day_entry['date']['gregorian']['weekday']['en']
            timings = day_entry['timings']
            daily_data.append({
                'day_num': day_entry['date']['gregorian']['day'],
                'day_name': day_name,
                'is_weekend': day_name in ['Saturday', 'Sunday'],
                'fajr': format_time(timings['Fajr']),
                'dhuhr': format_time(timings['Dhuhr']),
                'asr': format_time(timings['Asr']),
                'maghrib': format_time(timings['Maghrib']),
                'isha': format_time(timings['Isha']),
            })

        monthly_data.append({
            'name': MONTHS[m_idx - 1],
            'days': daily_data
        })
    return monthly_data


def generate_pdf(template, monthly_data, year, location):
    html_content = template.render(
        location_title=location.short,
        year=year,
        months=monthly_data
    )
    output_filename = f'{location.short}_prayer_times_{year}.pdf'.lower()
    weasyprint.HTML(string=html_content).write_pdf(output_filename)
    print(f'Generated {output_filename}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate monthly Islamic prayer times for LOC at YEAR')
    parser.add_argument('-y', '--year', type=int, help='The year', required=True)
    parser.add_argument('-l', '--location', metavar='LOC', help='The location', default='newcastle')
    args = parser.parse_args()

    with open(PRAYER_TIMES_TEMPLATE, 'r', encoding='utf-8') as f:
        template_str = f.read()

    template = Template(template_str)
    location = get_location(args.location)
    raw_data = load_prayer_times_data(args.year, location)
    monthly_data = to_monthly_data(raw_data)
    generate_pdf(template, monthly_data, args.year, location)


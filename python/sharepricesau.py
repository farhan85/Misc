#!/usr/bin/env python

import argparse
import csv
import json
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import urlopen


def to_epoch(dt):
    return int(dt.timestamp())


def from_iso_str(s):
    return datetime.fromisoformat(s.replace('Z','')).astimezone(timezone.utc)


def gen_url_yahoo(symbol, epoch_start, epoch_end):
    symbol = f'{symbol}.AX'.upper()
    base_url = f'https://au.finance.yahoo.com/quote/{symbol}/history'
    query = urlencode({
        'period1': epoch_start,
        'period2': epoch_end,
        'interval': '1d',
        'filter': 'history',
        'frequency': '1d',
        'includeAdjustedClose': True
    })
    return f'{base_url}?{query}'


def get_data_yahoo(symbol, epoch_start, epoch_end):
    symbol = f'{symbol}.AX'.upper()
    base_url = f'https://query1.finance.yahoo.com/v7/finance/download'
    query = urlencode({
        'period1': epoch_start,
        'period2': epoch_end,
        'interval': '1d',
        'events': 'history',
        'includeAdjustedClose': True
    })
    with urlopen(f'{base_url}/{symbol}?{query}') as response:
        return response.read().decode('utf-8')


def list_share_prices(symbols, epoch_start, epoch_end):
    print('Symbol', 'Date', 'Close[AUD]')
    for symbol in (s.upper() for s in symbols):
        data = get_data_yahoo(symbol, epoch_start, epoch_end)
        reader = csv.DictReader(data.splitlines())
        quotes = sorted(reader,
                       key=lambda q: datetime.strptime(q['Date'], '%Y-%m-%d'),
                       reverse=True)
        quote = quotes[0]
        print(symbol, quote['Date'], '{:.2f}'.format(Decimal(quote['Close'])))


def get_forex_tiingo(ticker, start_date, end_date, token):
    base_url = f'https://api.tiingo.com/tiingo/fx/{ticker}/prices'
    query = urlencode({
        'startDate': start_date.strftime('%Y-%m-%d'),
        'endDate': end_date.strftime('%Y-%m-%d'),
        'resampleFreq': '1day',
        'token': token
    })
    with urlopen(f'{base_url}?{query}') as response:
        return response.read().decode('utf-8')


def print_exchange_rate(forex_name, start_date, end_date, token):
    ticker = forex_name.replace('/', '').lower()
    quotes = get_forex_tiingo(ticker, dt_start, dt_end, token)
    quotes = sorted(json.loads(quotes),
                    key=lambda q: from_iso_str(q['date']),
                    reverse=True)
    quote = quotes[0]
    print(forex_name,
          from_iso_str(quote['date']).strftime('%Y-%m-%d'),
          '{:.2f}'.format(Decimal(quote['close'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='''Retrieves Aussie share values at the end of a given
            year. Helpful for declaring foreign finances for US tax purposes''')

    parser.add_argument('-s', '--symbols', required=True,
                        help='CSV string of share symbols to retrieve data for')
    parser.add_argument('-t', '--token', required=True,
                        help='Tiingo API token')
    parser.add_argument('-y', '--year', type=int, required=True,
                        help='[End of] year to retrieve prices for')
    args = parser.parse_args()

    dt_start = datetime(args.year, 12, 29, tzinfo=timezone.utc)
    dt_end = datetime(args.year, 12, 31, tzinfo=timezone.utc)

    list_share_prices(args.symbols.split(','), to_epoch(dt_start), to_epoch(dt_end))
    print()
    print_exchange_rate('AUD/USD', dt_start, dt_end, args.token)
    print()
    print('Historical share prices, e.g.')
    print(gen_url_yahoo('CBA', to_epoch(dt_start), to_epoch(dt_end)))
    print()
    print('Historical AUD/USD exchange rates:')
    print('https://investing.com/currencies/aud-usd-historical-data')
    print()
    print('Submit FBAR report of foreign finances at:')
    print('https://bsaefiling.fincen.treas.gov/NoRegFBARFiler.html')

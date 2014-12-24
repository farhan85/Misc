"""
"""

import argparse
from ConfigParser import ConfigParser, NoOptionError
import logging
import traceback

from db_models import DB, add_teams
import log_config
from nrl_stats_scraper import NrlScraper


log = logging.getLogger("run_scraper_main")

DESCRIPTION = '''NRL data scrapper and (hopefully good) result predictor.
Match info is retrieved from www.nrlstats.com
Results predictor is done by Monte-Carlo analysis
'''
VERSION = '1.0'

CONFIG_SECTION_GENERAL = 'general'
DEFAULT_CONFIG_FILE = 'config.cfg'
CONFIG_BASE_URL = 'base_url'
CONFIG_DB_URL = 'database_url'
CONFIG_SEASON_PAGE = 'season_page'
CONFIG_YEAR_FIRST = 'year_first'
CONFIG_YEAR_LAST = 'year_last'

def main():

    parser = argparse.ArgumentParser(description=DESCRIPTION, version=VERSION)

    parser.add_argument('-t', '--add_teams', action='store_true', default=False, help='Adds all the teams to the database')
    parser.add_argument('-c', '--config-file', action='store', default=DEFAULT_CONFIG_FILE, help='The config file')

    results = parser.parse_args()

    config = ConfigParser()
    parsed_config_files = config.read(results.config_file)
    if not parsed_config_files:
        print 'Could not load config file "{0}"'.format(results.config_file)

    try:
        log.info("Loading config")
        db_url = config.get(CONFIG_SECTION_GENERAL, CONFIG_DB_URL)
        base_url = config.get(CONFIG_SECTION_GENERAL, CONFIG_BASE_URL)
        season_url = config.get(CONFIG_SECTION_GENERAL, CONFIG_SEASON_PAGE)
        year_first = int(config.get(CONFIG_SECTION_GENERAL, CONFIG_YEAR_FIRST))
        year_last = int(config.get(CONFIG_SECTION_GENERAL, CONFIG_YEAR_LAST))
    except NoOptionError, e:
        log.exception("Could not find an expected config option in the file")
        return
    except ValueError, e:
        log.exception("Could not convert a config value to an int")
        return

    log.info("Creating DB ORM")
    db = DB(db_url)

    if results.add_teams:
        log.info("Adding teams to the DB")
        with db.session_scope() as session:
            add_teams(session)

    nrl_scraper = NrlScraper(base_url, db, season_url)
    for year in range(year_first, year_last+1):
        nrl_scraper.scrape_season_webpage(year)


if __name__ == '__main__':
    log.info("Start NRL stats scraper")
    try:
        main()
    except:
        log.exception("Unhandled exception thrown")
    log.info("Finish NRL stats scraper")
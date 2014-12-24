"""
"""

from dateutil.parser import parse
import logging
import re
import sys
import urlparse

from lxml import html
from lxml.etree import tostring
import requests
from sqlalchemy.exc import SQLAlchemyError

from db_models import get_or_create, Match, Player, PlayerMatchStats,\
    Team, TeamMatchStats
import log_config


log = logging.getLogger(__name__)
# TODO: Add logging.debug(...) statements

class NrlScraper(object):

    def __init__(self, base_url, db, season_url):
        self.base_url = base_url
        self.db = db
        self.season_url = season_url

        self.report2_match_stats = (
            (1, re.compile(r'(\d+)halftime(\d+)'), 'halftime_score'),
            (2, re.compile(r'(\d+)penalties(\d+)'), 'penalties'),
            (3, re.compile(r'(\d+)scrums(\d+)'), 'scrums'),
            (4, re.compile(r'(\d+).+comp\/sets\(%\)(\d+)'), 'completed_sets'),
            (4, re.compile(r'\d+\s*\/\s*(\d+).+comp\/sets\(%\)\d+\s*\/\s*(\d+)'), 'total_sets'),
            (5, re.compile(r'(\d+)tackles(\d+)'), 'tackles'),
            (6, re.compile(r'(\d+)missed tackles(\d+)'), 'missed_tackles'),
            #(7, re.compile(r'(\d+)hit-ups(\d+)'), ''),
            #(8, re.compile(r'(\d+)line breaks(\d+)'), ''),
            #(9, re.compile(r'(\d+)kicks(\d+)'), ''),
            #(10, re.compile(r'(\d+)offloads(\d+)'), ''),
            #(11, re.compile(r'(\d+)errors(\d+)'), ''),
            (12, re.compile(r'(\d+)%possesion(\d+)%'), 'possession'),
            )

        self.report2_row_tries = 16
        self.report2_row_goals = 17

        self.report2_p_tries = re.compile(r'([a-zA-z\s-]+)\d+m,?')
        self.report2_p_goals = re.compile(r'([a-zA-z\s-]+)(\d+)/(\d+)')

        self.p_all = re.compile(r'(.*)')
        self.p_first_val = re.compile(r'(\d+)[^\d]*')
        self.p_second_val = re.compile(r'\d+\s*\[(\d+)[^\d]*\]')
        # (?P=<name>...)

        self.report3_player_stats = (
            #(1, 'name', self.p_all),
            (2, 'tackles', self.p_first_val),
            (2, 'missed_tackles', self.p_second_val),
            (3, 'runs_total', self.p_first_val),
            (3, 'runs_metres', self.p_second_val),
            (4, 'line_breaks', self.p_first_val),
            (5, 'offloads', self.p_first_val),
            (6, 'errors', self.p_first_val),
            (7, 'penalties_conceded', self.p_first_val),
            )

    def parse_rel_link(self, rel_link):
        """Parses the given nrlstats relative link."""
        url = self.base_url + rel_link
        response = requests.get(url)
        return html.fromstring(response.text)

    def extract_from_report2(self, session, match_id, home_team_id, away_team_id, rel_link):
        log.info("Analysing Report 2 for match {} found at {}".format(match_id, rel_link))
        parsed_html = self.parse_rel_link(rel_link)
        #parsed_html = html.parse('report2.html')

        home_stats = get_or_create(session, TeamMatchStats, match_id=match_id, team_id=home_team_id)
        away_stats = get_or_create(session, TeamMatchStats, match_id=match_id, team_id=away_team_id)

        # Match summary is in <table class='tablec'>
        match_stats_table = parsed_html.xpath("//table[@class='tablec'][1]")[0]
        rows = match_stats_table.xpath("./tr")
        for stat in self.report2_match_stats:
            m = stat[1].match(rows[stat[0]].text_content().lower())
            if m:
                setattr(home_stats, stat[2], m.group(1))
                setattr(away_stats, stat[2], m.group(2))

        # Extract tries
        # There are three <td>'s. The first has the home team's try scorers,
        # The second has the title 'Tries' (we ignore this one), and the last
        # one has the away team's try scorers.
        tds = rows[self.report2_row_tries].xpath('./td')
        combo = ((tds[0].text, home_team_id), (tds[2].text, away_team_id))
        for c in combo:
            for player_name in self.report2_p_tries.findall(c[0]):
                player = get_or_create(session, Player,
                    name=player_name.strip(), team_id=c[1])
                player_stats = get_or_create(session, PlayerMatchStats,
                    player=player, match_id=match_id)
                log.debug("{} scored a try".format(repr(player)))
                log.debug(repr(player_stats))
                player_stats.tries = player_stats.tries + 1

        # Extract goals
        # Three <td>'s similar to the 'Tries' row.
        tds = rows[self.report2_row_goals].xpath('./td')
        combo = ((tds[0].text, home_team_id), (tds[2].text, away_team_id))
        for c in combo:
            for player_name, success, total in self.report2_p_goals.findall(c[0]):
                player = get_or_create(session, Player, name=player_name.strip(),
                    team_id=c[1])
                player_stats = get_or_create(session, PlayerMatchStats,
                    player_id=player.id, match_id=match_id)
                player_stats.penalty_goals = player_stats.penalty_goals + int(success)

    def extract_from_report3(self, session, match_id, home_team_id, away_team_id, rel_link):
        log.info("Analysing Report 3 for match {} found at {}".format(match_id, rel_link))
        parsed_html = self.parse_rel_link(rel_link)

        # Home team is in first table
        stats_tables = parsed_html.xpath("//table[@class='tablec']")
        teams = (
            (home_team_id, stats_tables[0]),
            (away_team_id, stats_tables[1]),
            )

        for team_id, table in teams:
            rows = table.xpath("./tr")
            for row in rows[1:]:
                td = row.xpath("./td")
                player = get_or_create(session, Player,
                    name=td[1].text_content(), team_id=team_id)
                for att in self.report3_player_stats:
                    m = att[2].match(td[att[0]].text_content())
                    if m:
                        player_stats = get_or_create(session, PlayerMatchStats,
                            player_id=player.id, match_id=match_id)
                        setattr(player_stats, att[1], m.group(1))

    def scrape_season_webpage(self, year):
        """
        """

        #parsed_html = html.parse('season2013.html')
        parsed_html = self.parse_rel_link(self.season_url.format(year=year))

        log.info("Scraping year {}".format(year))

        # Each <div class='m_nrl'> contains information for a round
        all_rounds = parsed_html.xpath("//div[contains(@class,'m_nrl')]")
        for round_info_div in all_rounds:

            # The round number is in a <div class='m_h'><span>
            round_no = round_info_div.xpath("./div[@class='m_h']/span/text()")[0].title()

            # The <div class='m_b'> is the actual div containing the round info
            round_info = round_info_div.xpath("./div[@class='m_b']")[0]

            # Each match info is in a <tr class='r0'> or <tr class='r1'>
            match_info_rows = round_info.xpath("./table/tr[@class='r0' or @class='r1']")
            for match_info in match_info_rows:

                # The first <td> has the date
                date = parse(match_info.xpath("./td[1]/text()")[0]).date()

                # The anchors contain the remaining information
                a_href = match_info.xpath("./td/a")

                # The first anchor has the two teams
                home_team, away_team = a_href[0].text.split(' v ')

                # We have enough info to create a match entry
                with self.db.session_scope() as session:
                    h = get_or_create(session, Team, name=home_team)
                    a = get_or_create(session, Team, name=away_team)
                    m = get_or_create(session, Match, year=year,
                        round=round_no, date=date, home_team=h, away_team=a)
                    log.info("Collecting info about {}, ID: {}".format(m, m.id))
                    home_team_id = h.id
                    away_team_id = a.id
                    match_id = m.id

                log.debug("home_team_id = {}, away_team_id = {}, match_id = {}".format(home_team_id, away_team_id, match_id))
                # The remaining anchors have the match reports
                for a in a_href[1:]:
                    rel_link = a.get('href')

                    with self.db.session_scope() as session:
                        try:
                            if a.text == '2':
                                self.extract_from_report2(session, match_id, home_team_id, away_team_id, rel_link)
                            elif a.text == '3':
                                self.extract_from_report3(session, match_id, home_team_id, away_team_id, rel_link)
                        except SQLAlchemyError, e:
                            # TODO: Log the error, and continue on
                            log.exception(e)

                # TODO: Remove this when done debugging
                #return
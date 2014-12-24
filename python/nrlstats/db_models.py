"""
Database ORM models.
"""

from contextlib import contextmanager
import logging
import os

from sqlalchemy import create_engine, Column, Date, ForeignKey, Index,\
    Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session

import log_config


log = logging.getLogger(__name__)
Base = declarative_base()

class Team(Base):
    """An NRL team"""

    __tablename__ = 'team'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    def __str__(self):
        return "Team[{0}]".format(self.name)

    def __repr__(self):
        return "Team(name='{0}')".format(self.name)


class Player(Base):
    """An NRL player"""

    __tablename__ = 'player'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    team_id = Column(Integer, ForeignKey('team.id'))

    team = relationship(Team)

    __table_args__ = (
        Index('idx_player', 'name', 'team_id'),
        )

    def __str__(self):
        return "Player[{0}]".format(self.name)

    def __repr__(self):
        return "Player(name='{0}')".format(self.name)


class Match(Base):
    """Defines a match between two teams"""

    __tablename__ = 'match'
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    round = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    home_team_id = Column(Integer, ForeignKey('team.id'), nullable=False)
    away_team_id = Column(Integer, ForeignKey('team.id'), nullable=False)

    home_team = relationship(Team, primaryjoin='Match.home_team_id == Team.id')
    away_team = relationship(Team, primaryjoin='Match.away_team_id == Team.id')

    __table_args__ = (
        UniqueConstraint('year', 'round', 'home_team_id', name='_uc_year_round_hometeam'),
        )

    def __str__(self):
        return "Match[{0}, {1}, {2} v {3}]".format(self.round, self.year,
            self.home_team, self.away_team)

    def __repr__(self):
        return "Match(year={0}, round={1}, date={2}, home_team_id={3}, "\
            + "away_team_id={4})".format(self.year, self.round, self.date,
            self.home_team, self.away_team)


class TeamMatchStats(Base):
    """Team stats for each match"""

    __tablename__ = 'team_match_stats'
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('team.id'), nullable=False)
    match_id = Column(Integer, ForeignKey('match.id'), nullable=False)
    score = Column(Integer, server_default='0', nullable=False)
    halftime_score = Column(Integer, server_default='0', nullable=False)
    penalties = Column(Integer, server_default='0', nullable=False)
    scrums = Column(Integer, server_default='0', nullable=False)
    completed_sets = Column(Integer, server_default='0', nullable=False)
    total_sets = Column(Integer, server_default='0', nullable=False)
    tackles = Column(Integer, server_default='0', nullable=False)
    missed_tackles = Column(Integer, server_default='0', nullable=False)
    possession = Column(Integer, server_default='0', nullable=False)

    match = relationship(Match)

    __table_args__ = (
        UniqueConstraint('team_id', 'match_id', name='_uc_team_match'),
        )

    def __str__(self):
        return "MatchStats[match_id={0} team_id={1}]".format(self.match_id, self.team_id)

    def __repr__(self):
        return "MatchStats(team_id={0}, match_id={1}, score={2}, "\
            + "halftime_score={3}, penalties={4}, scrums={5}, "\
            + "completed_sets={6}, total_sets={7}, tackles={8}, "\
            + "missed_tackles={9}, possession={10})".format(
                self.team_id,
                self.match_id,
                self.score,
                self.halftime_score,
                self.penalties,
                self.scrums,
                self.completed_sets,
                self.total_sets,
                self.tackles,
                self.missed_tackles,
                self.possession
                )


class PlayerMatchStats(Base):
    """Player stats for each match"""

    __tablename__ = 'player_match_stats'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('player.id'), nullable=False)
    match_id = Column(Integer, ForeignKey('match.id'), nullable=False)
    tackles = Column(Integer, server_default='0', nullable=False)
    missed_tackles = Column(Integer, server_default='0', nullable=False)
    hit_ups = Column(Integer, server_default='0', nullable=False)
    offloads = Column(Integer, server_default='0', nullable=False)
    line_breaks = Column(Integer, server_default='0', nullable=False)
    errors = Column(Integer, server_default='0', nullable=False)
    runs_total = Column(Integer, server_default='0', nullable=False)
    runs_metres = Column(Integer, server_default='0', nullable=False)
    penalties_conceded = Column(Integer, server_default='0', nullable=False)
    tries = Column(Integer, server_default='0', nullable=False)
    penalty_goals = Column(Integer, server_default='0', nullable=False)
    field_goals = Column(Integer, server_default='0', nullable=False)

    player = relationship(Player)
    match = relationship(Match)

    __table_args__ = (
        UniqueConstraint('player_id', 'match_id', name='_uc_player_match'),
        )

    def __str__(self):
        return "PlayerMatchStats[player_id={0}, match_id={1}]".format(
            self.player_id, self.match_id)

    def __repr__(self):
        return "PlayerMatchStats(player_id={}, match_id={}, tackles={}, "\
            + "missed_tackles={}, hit_ups={}, offloads={}, "\
            + "line_breaks={}, errors={}, runs_total={}, runs_metres={}, "\
            + "penalties_conceded={}, tries={}, penalty_goals={}, "\
            + "field_goals={})".format(
                self.player_id,
                self.match_id,
                self.tackles,
                self.missed_tackles,
                self.hit_ups,
                self.offloads,
                self.line_breaks,
                self.errors,
                self.runs_total,
                self.runs_metres,
                self.penalties_conceded,
                self.tries,
                self.penalty_goals,
                self.field_goals
                )

class DB(object):

    def __init__(self, database_url):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""

        sm = sessionmaker(bind=self.engine)
        session = scoped_session(sm)
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    log.debug("get_or_create({}, {})".format(model, kwargs))
    if instance:
        return instance
    else:
        log.debug("Creating new instance")
        instance = model(**kwargs)
        session.add(instance)
        # Make sure we have the newly assigned primary key
        session.flush()
        return instance


def add_teams(session):
    log.info("Creating new teams")
    get_or_create(session, Team, name='Brisbane')
    get_or_create(session, Team, name='Canberra')
    get_or_create(session, Team, name='Canterbury-Bankstown')
    get_or_create(session, Team, name='Cronulla')
    get_or_create(session, Team, name='Gold Coast')
    get_or_create(session, Team, name='Manly')
    get_or_create(session, Team, name='Melbourne')
    get_or_create(session, Team, name='Newcastle')
    get_or_create(session, Team, name='North Queensland')
    get_or_create(session, Team, name='Parramatta')
    get_or_create(session, Team, name='Penrith')
    get_or_create(session, Team, name='South Sydney')
    get_or_create(session, Team, name='St George Illawarra')
    get_or_create(session, Team, name='Sydney Roosters')
    get_or_create(session, Team, name='Warriors')
    get_or_create(session, Team, name='Wests Tigers')
"""
This class is a wrapper to the trailer database, allowing us to add {movie,youtube video ID} pairs
into the database.
"""

from sqlalchemy import *
from sqlalchemy.orm import mapper, sessionmaker

import logging
import trailer_logger

logger = logging.getLogger(__name__)
logger.addHandler(trailer_logger.LOG_FILE_HANDLER)

class Movie(object):
	"""
	The class used to model the rows of the ``movies`` table.
	"""
	pass

class State(object):
	"""
	The class used to model the rows of the ``movies`` table.
	"""
	pass

class DB:
	"""
	The database wrapper.

	Sample usage:

	db = trailer_db.DB("trailers_db.sqlite")
	session = db.new_session()
	current_movie = db.get_movie(session, "X-Men")
	if current_movie.video_id is None:
		# We haven't found a trailer yet for this movie, so add one
		# Assign the video www.youtube.com/watch?v=abcdefgh to this movie
		current_movie.video_id = "abcdefg"
		db.update_changes(session)

	db.close_session(session)

	Attributes:
		Session - A session factory.
	"""

	def __init__(self, sqlite_file):
		"""
		Creates a new sqlite file to use as the database.

		Parameters:
			sqlite_file - The filename of the Sqlite file to create/read
		"""

		logger.debug("Initialising database in file {0}".format(sqlite_file))

		db_engine = create_engine('sqlite:///{0}'.format(sqlite_file))
		db_engine.echo = False

		# Create the object to manage table definitions
		metadata = MetaData(db_engine)

		movies = Table('movies', metadata,
			Column('id', Integer, primary_key=True),
			Column('title', String(40), nullable=False, unique=True),
			Column('video_id', String(40), nullable=True, default=null())
		)

		state = Table('state', metadata,
			Column('id', Integer, primary_key=True),
			Column('key', String(40), unique=True),
			Column('value', String(40), nullable=True, default=null())
		)

		# Finally create all our tables
		metadata.create_all()

		movie_mapper = mapper(Movie, movies)
		state_mapper = mapper(State, state)

		# Create Session factory
		self.Session = sessionmaker(bind=db_engine)

	def new_session(self):
		"""
		Creates and returns a new session, which is needed to push changes to the database.

		The session object needs to be closed with the ``DB.close_session(self, session)`` function.

		Returns:
			A new session object.
		"""

		# Start a new session and return it
		return self.Session()

	def close_session(self, session):
		"""
		Closes the specified session.
		"""

		session.close()

	def update_changes(self, session):
		"""
		Pushes changes made to DB model objects (e.g. ``trailer_db.Movie``) to the database.

		Parameters:
			session - A DB session object
		"""
		session.commit()

	def get_movie(self, session, movie_title):
		"""
		Gets a ``trailer_db.Movie`` object representing the specified movie (``movie_title``)
		from the database.

		A new movie entry will be created if needed.

		Parameters:
			session     - A DB session object
			movie_title - The title of the movie whose details should be retrieved from the database

		Returns:
			A ``trailer_db.Movie`` object representing the specified movie from the database
		"""

		logger.debug('Retriving movie with title "{0}"'.format(movie_title))
		old_movies = session.query(Movie).filter(Movie.title == movie_title)

		if old_movies.count() == 0:
			logger.debug("Couldn't find one, so creating a new entry in DB")
			current_movie = Movie()
			current_movie.title = movie_title
			session.add(current_movie)
			# Write saved data to db
			session.commit()
		else:
			current_movie = old_movies[0]

		return current_movie

	def get_state(self, session, key):
		"""
		Gets a ``trailer_db.State`` object representing the specified key/value pair stored in the ``state`` table.

		A new state entry will be created if needed.

		Parameters:
			session - A DB session object
			key     - key, for which the currently stored key/value pair will be returned

		Returns:
			A ``trailer_db.State`` object representing the key/value pair stored in the database
		"""

		logger.debug('Retriving key/value for key="{0}"'.format(key))
		old_states = session.query(State).filter(State.key == key)

		if old_states.count() == 0:
			logger.debug("Couldn't find one, so creating a new entry in DB")
			current_state = State()
			current_state.key = key
			session.add(current_state)
			# Write saved data to db
			session.commit()
		else:
			current_state = old_states[0]

		return current_state
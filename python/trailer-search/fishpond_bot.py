"""
This module searches the fishpond website for videos that don't have movie trailers.
"""

import logging
import lxml.html
import re
import requests
import trailer_db
import trailer_logger
import youtube_search
from proxies import Proxies


logger = logging.getLogger(__name__)
logger.addHandler(trailer_logger.LOG_FILE_HANDLER)


class MovieInfo:
	"""
	Contains information about what is known about a certain movie in the fishpond website

	Attributes:
		url          - The fishpond URL of this movie
		title        - The main title of this movie
		subtitle     - The subtitle of this movie
		has_trailers - Whether or not the fishpond site has trailers for the given movie
		has_data     - Whether or not data was actually retrieved from the fishpond website
	"""

	def __init__(self, url):
		self.url = url
		self.title = ""
		self.subtitle = ""
		self.has_trailers = False
		self.has_data = False

		# Extract the video ID from the url
		pattern = re.compile("([^/]+)$")
		ids = re.findall(pattern, self.url)
		if len(ids) > 0:
			self.id = ids[0]

	def full_title(self):
		return "{0} {1}".format(self.title, self.subtitle)

	def __str__(self):
		return "URL: {0}\nTitle: {1}\nSubtitle: {2}\nHas Trailers: {3}".format(self.url, self.title, self.subtitle, self.has_trailers)

class FishpondBot:
	"""
	A bot which goes through Movie lists in the fishpond website.
	"""

	SEARCH_PAGE_URL = "http://www.fishpond.com.au/{0}/?cName={0}&outprint=1&page={1}"
	LOGIN_URL = "https://www.fishpond.com.au/login.php?action=process"
	SUBMIT_TRAILER_URL = "https://www.fishpond.com.au/add_trailer.php"

	def __init__(self, trailer_type, username, password):
		"""
		Creates a new ``FishpondBot`` for finding trailers.

		Parameters:
			trailer_type - What we are search trailers for? Movies, Games, ...
			username     - The username to use when logging into the fishpond website
			password     - The password to use when logging into the fishpond website
		"""
		self.trailer_type = trailer_type

		# Log into the fishpond website and maintain the session
		payload = {
			'email_address': username,
			'password': password
		}
		self.session = requests.Session()

		logger.info("Logging into Fishpond")
		r = self.session.post(FishpondBot.LOGIN_URL, data=payload)
		if 'Sign In to continue' in r.text:
			logger.warn("Log in failed")
		else:
			logger.info("Login successful")

	def run(self, num_search_pages, first_start_page=0):
		"""
		Gets the list of movies, loads each web page and checks if there are any movie trailers.

		Parameters:
			num_search_pages - The number of search pages to go through
			first_start_page - (Optional) The first search page to start from. If not provided, the
							   program will continue from the last search page it parsed.
		"""
		db = trailer_db.DB("trailers_db.sqlite")
		session = db.new_session()

		last_start_page = db.get_state(session, 'last_start_page')
		if last_start_page.value is None:
			last_start_page.value = 0
		if first_start_page > 0:
			last_start_page.value = first_start_page - 1

		first_search_page_num = int(last_start_page.value) + 1
		for page_num in range (first_search_page_num, first_search_page_num + num_search_pages):
			logger.info("Retrieving search page #{0}".format(page_num))

			# Get the next list of movies
			r = requests.get(FishpondBot.SEARCH_PAGE_URL.format(self.trailer_type, page_num), proxies=Proxies.default_proxy)

			if r.status_code == requests.codes.ok:
				# Get a list of all movies on the current search page
				movie_urls = self.parse_search_results(r.text)

				for url in movie_urls:
					try:
						# Get info about the movie
						movie_info = self.parse_movie_page(url)
						logger.debug('Found movie "{0}". Has trailers? {1}'.format(movie_info.full_title(), "Yes" if movie_info.has_trailers else "No"))

						if movie_info.has_data:
							# If the movie does not have trailers, and we found a Youtube video,
							# submit the Youtube video as a movie trailer.
							if not movie_info.has_trailers:
								# Check if we haven't already submitted a trailer already for this movie
								current_movie = db.get_movie(session, movie_info.full_title())

								if current_movie.video_id is None:
									# We haven't found a trailer yet for this movie, so search for one
									logger.debug('Trailer has not been submitted for "{0}" yet'.format(movie_info.full_title()))

									ys = youtube_search.TrailerSearch(movie_info.full_title())
									youtube_vid = ys.movie_trailer()

									if youtube_vid.found:
										logger.debug("Found this Youtube video: {0}".format(str(youtube_vid)))

										# Save an entry in our database (so we don't resubmit the same trailer again)
										current_movie.video_id = youtube_vid.video_id
										db.update_changes(session)

										# Submit the video to the fishpond website
										self.submit_movie_trailer(movie_info, youtube_vid)

									else: # youtube_vid.found = False
										logger.warn('Couldn\'t find trailer on Youtube for "{0}"'.format(movie_info.full_title()))

								else: # current_movie.video_id is not None:
									logger.info('Trailer for "{0}" already submitted'.format(movie_info.full_title()))
					except Exception as e:
						logger.error("{0}\n{1}".format(e.__doc__, e.message), exc_info=True)
			else:
				logger.warn("Could not retrieve movie list from fishpond website.")

			last_start_page.value = page_num
			db.update_changes(session)

		logger.info("Finished searching for trailers")
		db.close_session(session)

	def parse_search_results(self, html_str):
		"""
		Parses a string containing the HTML source of the search results from the fishpond website,
		and returns a list of all the movies from the search results.

		Parameters:
			html_str - The HTML source of the search results web page from the fishpond website

		Returns:
			A list containing the URLs of the movies (fishpond webpages of each movie)
		"""

		pattern = re.compile(r'<td.*class="productSearch-data productSearch-highlight-left".*<a href="(.*)">.*</td>')
		movie_urls = re.findall(pattern, html_str)
		return movie_urls

	def parse_movie_page(self, url):
		"""
		Parses the fishpond webpage and checks if there are any trailers posted.

		Parameters
			url - The fishpond webpage to parse

		Returns
			A ``MovieInfo`` containing the results of the parse
		"""

		r = requests.get(url, proxies=Proxies.default_proxy)
		m_info = MovieInfo(url)


		if r.status_code == requests.codes.ok:
			if r'<h4 class="field_label">Trailer</h4>' in r.text:
				m_info.has_trailers = True
			else:
				m_info.has_trailers = False

			htmldom = lxml.html.document_fromstring(r.text)

			# The movie title is found in an HTML element like this:
			# <h1 id="product_title"><span itemprop="name" class="fn">MOVIE TITLE</span></h1>
			elements = htmldom.get_element_by_id('product_title')
			elements = elements.findall("span[@class='fn']")
			if len(elements) > 0:
				m_info.title = elements[0].text_content()

			# The movie subtitle (if it has one) is found in an HTML element like this:
			# <p id="product_subtitle">MOVIE SUBTITLE</p>
			elements = htmldom.get_element_by_id('product_subtitle', None)
			if elements is not None:
				m_info.subtitle = elements.text_content()

			m_info.has_data = True

		else:
			m_info.has_data = False
			logger.warn("Could not retrieve movie page ({0}) from fishpond website.".format(url))

		return m_info

	def submit_movie_trailer(self, movie_info, youtube_vid):
		logger.info('Submitting {{"{0}","{1}"}}'.format(movie_info.title, youtube_vid.html_url))
		payload = {
			'trailer_link' : youtube_vid.embedded_code(),
			'id' : movie_info.id
		}
		reponse = requests.post(FishpondBot.SUBMIT_TRAILER_URL, data=payload)

"""
This module searches Youtube for videos (in particular, movie trailers)
"""

# Youtube uses unicode strings, so we default to using them too.
from __future__ import unicode_literals

import logging
import re
import requests
import trailer_logger
from proxies import Proxies


logger = logging.getLogger(__name__)
logger.addHandler(trailer_logger.LOG_FILE_HANDLER)


class YoutubeVideo:
	"""
	Represents a Youtube video from the web.

	Attributes:
		found         - Boolean value indicating whether or not a movie trailer was found
		title         - The title of the movie trailer
		videl_id      - The video ID of the Youtube video
		video_url     - The URL of the video itself (which can be embedded in a web page)
		html_url      - The URL of a HTML web page where the video can be seen.
		is_widescreen - Whether the video's aspect ratio is widescreen or letterbox.
	"""

	def __init__(self):
		self.found = False
		self.title = ""
		self.video_id = ""
		self.video_url = ""
		self.html_url = ""
		is_widescreen = True

	def set_url(self, video_url=None, html_url=None):
		if not video_url is None:
			self.video_url = video_url.replace('&app=youtube_gdata','')

		if not html_url is None:
			self.html_url = html_url.replace('&feature=youtube_gdata', '')

	def embedded_code(self):
		"""
		Returns the html code for embedding this Youtube video on a page.
		"""

		if self.is_widescreen:
			w = '640px'
			h = '360px'
		else:
			w = '480px'
			h = '360px'

		code = (
			'<iframe '
			'width="{0}" height="{1}" '
			'src="//www.youtube.com/embed/{2}" '
			'frameborder="0" allowfullscreen>'
			'</iframe>'
		)

		return code.format(w, h, self.video_id)

	def __str__(self):
		return "Title: {0}\nURL: {1}".format(self.title, self.html_url)


class TrailerSearch:
	"""
	Searches Youtube for a movie's trailer.

	Attributes:
		youtube_search_url - The URL of Youtube's web service.
	"""

	# Base URL
	youtube_search_url = "http://gdata.youtube.com/feeds/api/videos"

	# Regexes for cleaning up movie title strings
	pattern_regionN = re.compile(r'\[Region \d+]+')    # Removing "[Region N]" substrings
	pattern_sqbrackets = re.compile(r'\[[^\]]*\]\s*')  # Removing square brackets and contents

	def __init__(self, movie_title):
		"""
		Initialises this ``TrailerSearch`` object to search for the specified movie.

		Parameters:
			movie_title - The movie whose trailer this object will search for.
		"""

		# Cleanup the movie title string
		movie_title = TrailerSearch.pattern_regionN.sub('', movie_title)
		movie_title = TrailerSearch.pattern_sqbrackets.sub('', movie_title)

		self.movie_title = movie_title

	def youtube_search_params(self, hd = False):
		"""
		Returns the search parameters to add to the base URL
		"""

		params = {
			"q" : self.movie_title + " trailer",  # The search query
			"start-index" : 1,               # Just get the first result
			"max-results" : 1,               #    "              "
			"v" : 2,                         # Use Youtube API v2
			"alt" : "json",                  # Format of search results (JSON)
		}

		if hd:
			params['hd'] = "true"

		return params

	def search_for_youtube_video(self, search_params_dict):
		"""
		Searches for the movie trailer and returns a ``YoutubeVideo`` object of the search result.

		Parameters
			search_params_dict - The parameters to use when searching for a video from Youtube.

		Returns
			A ``YoutubeVideo`` object containing information about the video that was found in Youtube.
		"""

		# Search Youtube and get the first video from the list
		logger.info('Searching Youtube with query "{0}"'.format(search_params_dict['q']))
		r = requests.get(TrailerSearch.youtube_search_url, params=search_params_dict, proxies=Proxies.default_proxy)

		movie_trailer = YoutubeVideo()
		movie_trailer.found = False
		try:
			# Video from search result
			video = r.json()['feed']['entry'][0]

			movie_trailer.title = video['title']['$t']
			movie_trailer.video_id = video['media$group']['yt$videoid']["$t"]

			if 'yt$aspectRatio' in video['media$group']:
				movie_trailer.is_widescreen = True if video['media$group']['yt$aspectRatio']["$t"] == "widescreen" else False

			movie_trailer.set_url(video_url = video['content']['src'])
			movie_trailer.set_url(html_url = [x for x in video['link'] if x['rel'] == "alternate"][0]['href'])
			movie_trailer.found = True

		except ValueError:
			logger.warn("Could not retrieve video from Youtube. Returned value was not a valid JSON object")

		except KeyError, e:
			logger.warn('KeyError exception thrown. Youtube search results for "{0}" returned a JSON object in an unknown format'.format(search_params_dict['q']))
			logger.exception(e)

		return movie_trailer

	def is_correct_video(self, video_title):
		logger.debug('Checking if "{0}" sounds like what we\'re looking for'.format(video_title))
		# Check if we all the words in the movie title we want is also in the video title we found
		has_all_words = True
		words = self.movie_title.lower().split(' ')
		video_title_lower = video_title.lower()
		i = 0
		while i < len(words) and has_all_words:
			# Ignore four letter words or less like 'and' 'the', 'then'
			if (len(words[i]) > 4) and (words[i] not in video_title_lower):
				has_all_words = False
			i = i + 1

		# Set this to 'info' level so we have a log of which titles are deemed to be trailers
		# and which are not (this algorithm is ever-changing)
		logger.info('Are all the words in "{0}" found in "{1}"? {2}'.format(self.movie_title.lower(), video_title_lower, 'Yes' if has_all_words else 'No'))

		# Now check if this is a trailer
		if has_all_words:
			has_all_words = False
			if 'trailer' in video_title_lower:
				has_all_words = True
			elif 'promo' in video_title_lower:
				has_all_words = True

		logger.info('Is it a trailer? {0}'.format('Yes' if has_all_words else 'No'))
		return has_all_words

	def movie_trailer(self):
		"""
		Searches for the movie trailer and returns a ``YoutubeVideo`` object of the search result.

		Returns
			A ``YoutubeVideo`` object containing information about the video that was found in Youtube.
		"""

		logger.debug('Searching for HD trailer (for "{0}")'.format(self.movie_title))

		# Try to find an HD video first
		movie_trailer = self.search_for_youtube_video(self.youtube_search_params(True))

		# Check if we got the video we want
		if not self.is_correct_video(movie_trailer.title):
			logger.debug("Couldn't find HD trailer. Searching for SD version")

			# Try again, this time searching for standard def videos
			movie_trailer = self.search_for_youtube_video(self.youtube_search_params(False))

			if not self.is_correct_video(movie_trailer.title):
				logger.debug("Couldn't find SD trailer")
				# Oh well, we couldn't find the correct video
				movie_trailer.found = False

		if movie_trailer.found:
			logger.debug("found {0}".format(movie_trailer.title))
		else:
			logger.debug('Stopped searching for trailers for "{0}"'.format(self.movie_title))

		return movie_trailer
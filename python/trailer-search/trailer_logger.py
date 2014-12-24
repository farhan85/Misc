import logging, logging.handlers

LOG_FILE_HANDLER = None

def init(debug_screen_level, debug_file_level):
	global LOG_FILE_HANDLER

	logging._defaultFormatter = logging.Formatter(u"%(message)s")

	# Set screen logging level
	if debug_screen_level.lower() == "info":
		logging.basicConfig(level=logging.INFO)
	elif debug_screen_level.lower() == "debug":
		logging.basicConfig(level=logging.DEBUG)
	elif debug_screen_level.lower() == "warn":
		logging.basicConfig(level=logging.WARN)

	# Create a file handler
	#LOG_FILE_HANDLER = logging.FileHandler('trailer_search.log')
	LOG_FILE_HANDLER = logging.handlers.RotatingFileHandler('trailer_search.log', 'a', 104857600, 3)
	if debug_file_level.lower() == "info":
		LOG_FILE_HANDLER.setLevel(logging.INFO)
	elif debug_file_level.lower() == "debug":
		LOG_FILE_HANDLER.setLevel(logging.DEBUG)
	elif debug_file_level.lower() == "warn":
		LOG_FILE_HANDLER.setLevel(logging.WARN)

	# Restrict unwanted logs to the error level (to prevent screen/file pollution)
	logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.ERROR)

	# Create a logging format
	formatter = logging.Formatter(u'%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	LOG_FILE_HANDLER.setFormatter(formatter)

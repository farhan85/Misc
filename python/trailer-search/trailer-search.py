# Load the properties and initialise the loggers before importing any other module.
import trailer_logger
import prop_file_reader
import sys

# Load properties
default_file = "trailer_config.dat"
if len(sys.argv) == 2:
	if sys.argv[1] == '-h':
		print '''Usages:
	python {0} -h                  Display this help message
	python {0} [config filename]   Run trailer search using the specified config file
	python {0}                     Run trailer search using '{1}' as the config file
'''.format(sys.argv[0], default_file)
	else:
		props = prop_file_reader.read_file(sys.argv[1])
else:
	props = prop_file_reader.read_file(default_file)

# Setup logger
trailer_logger.init(props.get('debug_screen_level', 'info'), props.get('debug_file_level', 'debug'))

import fishpond_bot
import logging
from apscheduler.scheduler import Scheduler
import time, datetime
import getpass
import os


logger = logging.getLogger(__name__)
logger.addHandler(trailer_logger.LOG_FILE_HANDLER)


# Create the Fishpond bot
username = props.get('login_email') or raw_input('Email: ')
password = props.get('login_pass') or getpass.getpass('Password: ')

# Set the certificates file (should be bundled with this program)
os.environ['REQUESTS_CA_BUNDLE'] = 'cacert.pem'

# Login
fbot = fishpond_bot.FishpondBot(props.get('trailer_type', 'Movies'), username, password)

# Create the scheduler (the schedule is specified in the trailer_config.dat file)
scheduler = Scheduler()
scheduler.start()

def scheduled_job():
	logger.info("started scheduled job")
	fbot.run(int(props.get('num_search_pages', 1)), int(props.get('first_search_page', 0)))

if props['schedule_job'] == 'true':
	scheduler.add_cron_job(scheduled_job,
		year        = props['schedule_year'],
		month       = props['schedule_month'],
		day         = props['schedule_day'],
		week        = props['schedule_week'],
		day_of_week = props['schedule_day_of_week'],
		hour        = props['schedule_hour'],
		minute      = props['schedule_minute'],
		second      = props['schedule_second'])

	x = ''
	while x != 'q':
		print "Press q <enter> to quit"
		x = raw_input()
		x = x.lower();
else:
	scheduled_job()
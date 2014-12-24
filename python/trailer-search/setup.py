from cx_Freeze import setup,Executable

# include the modules being used
includes = ['__future__', 'apscheduler.scheduler', 'datetime', 'fishpond_bot', 'getpass', 'logging',
	'lxml', 'lxml.etree', 'lxml._elementpath', 'lxml.ElementInclude', 'lxml.html', 'prop_file_reader',
	'proxies', 're', 'requests', 'sqlalchemy', 'sqlalchemy.dialects.sqlite', 'sqlalchemy.orm', 'sys',
	'time', 'trailer_db', 'trailer_logger', 'youtube_search']

packages = []

include_files =["cacert.pem", ("trailer_config_prod.dat", "trailer_config.dat")]

# The main script (create a console application)
exe = Executable(
	script = "trailer-search.py",
	targetName = "fishpond-trailer-search.exe"
)

# The version number
setup (
	name = "fishpond-trailer-search",
	version = "2.0",
	description = "Searches the list of movies in the Fishpond website, searches for trailers in Youtube, then submits the found trailer",
	author = "Farhan Ahammed",
	options = {
		"build_exe": {
			"packages": packages,
			"includes": includes,
			"include_files": include_files
		}
	},
	executables = [exe]
)
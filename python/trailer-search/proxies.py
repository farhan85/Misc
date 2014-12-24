"""
This module defines proxies (to use when using the ``requests`` package)
"""

class Proxies:
	"""
	The various proxies are defined in this class.

	Attributes:
	__no_proxy    - To use when no proxies are requireds
	__usyd_proxy  - To use when connected to the Usyd LAN
	__usyd_proxy2 - Alternative Usyd proxy

	default_proxy is the attribute that should be used (and set here).
	"""

	__no_proxy = {}

	# Usyd proxy
	__usyd_proxy = {
		"http"  : "http://web-cache.usyd.edu.au:8080",
		"https" : "https://web-cache.usyd.edu.au:8080"
	}

	# Usyd proxy
	__usyd_proxy2 = {
		"http"  : "http://web-cache-ext.usyd.edu.au:8080",
		"https" : "https://web-cache-ext.usyd.edu.au:8080"
	}

	default_proxy = __no_proxy

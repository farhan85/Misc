"""
Contains classes that are used to read properties files.

The property file should have the format:

# This is a comment
# Only one key/value on each line
[key] = [value]
"""

def read_file(filename):
	properties = {}
	with open(filename) as prop_file:
		for line in prop_file:
			line = line.strip()
			if len(line) > 0 and line[0] <> '#' and '=' in line:
				tokens = line.split('=', 1)
				properties[tokens[0].strip()] = tokens[1].strip()

	return properties
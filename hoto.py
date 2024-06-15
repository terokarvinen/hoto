#!/usr/bin/python3
"""hoto - rename HTML and MAFF files from HTML tags and metadata

Prints new filenames: html h1 text. Keeps the existing suffix. 
This uses the default --format, which is '{h1}.{ext}'

	$ hoto foo.html bar.maff

Print top heading (h1) of each file. 

	$ hoto -f '{h1}' foo.html bar.maff

Print example variables you can use.

	$ hoto -s foo.html

Rename the files to HTML title, keeping existing suffix.

	$ hoto -f '{title}.{ext}' foo.html bar.maff --rename

## Advanced Usage

Hoto can extract HTML tags using CSS selectors. This is similar to jQuery and pyQuery. Hoto uses pyQuery library for tag extraction. 

	$ hoto.py tero.html --format="{sel.h2}"
	Python weppipalvelu - ideasta tuotantoon Palvelinten Hallinta Tunkeutumistestaus Information Security WebGoat with Podman Making Zero Days New Course: Network A	

All HTML tag extractions are also supported with MAFF archives

	$ hoto.py tero.maff --format="{title}"
	Tero Karvinen - Learn Free software with me

If you leave out curly brackets, they are added automatically.

	$ hoto.py tero.html -f sel.title
	Tero Karvinen - Learn Free software with me

All CSS selectors supported by pyQuery are available. For more complex selectors, use function syntax. Single quotes '' are required on function syntax. 

	$ ./hoto.py tero.html -f "sel('h2:first')" # single quotes required with sel('')
	Python weppipalvelu - ideasta tuotantoon

You can combine multiple variables and fixed text

	$ hoto.py tero.html -f "{stem} - {h1} - 2024.{ext}"
	tero - Tero Karvinen - 2024.htm

## Variable Types: HTML Tags with CSS Selectors

	$ hoto.py tero.html --format="{sel.h2}"
	$ hoto.py tero.html -f sel.title
	$ ./hoto.py tero.html -f "sel('h2:first')" # single quotes required with sel('')

## Variable Types: Shorthand

	$ ./hoto.py tero.html -f stem
	$ ./hoto.py tero.html -f h1
	$ ./hoto.py tero.html --format="{h1}"
	$ ./hoto.py tero.html -f ext

## Variable Types: RDF for MAFF Archives

MAFF is the Mozilla Archive Format. MAFF stores a whole page, including style 
sheets and images, into a single ZIP file. 

You can create MAFF files with Firefox WebScrapbook addon. Current hoto implementation 
of MAFF index.rdf parsing is only tested and developed with WebScrapbook. 

	$ hoto.py tero.maff -f '{rdf.archived} {rdf.originalurl} {rdf.host}'
	2024-06-15 w24 Sat https://terokarvinen.com/ terokarvinen.com

## Other

GNU General Public License, version 3. 

See you at https://TeroKarvinen.com

"""
__copyright__ = "GNU General Public License, version 3. Copyright 2024 Tero Karvinen http://TeroKarvinen.com"

import sys
assert sys.version_info.major >= 3
import os

import logging
from logging import info, debug, error, warning, INFO, WARNING, DEBUG
import argparse
from pathlib import Path

from types import SimpleNamespace
from datetime import datetime
import re
import zipfile
from lxml import etree
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
import unicodedata

from pyquery import PyQuery as pq # apt-get install python3-pyquery
from rdflib import Graph # apt-get install python3-rdflib

### Argument parsing ###

class TFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    """Combine multiple argparse formatters.
    Default values are only shown for arguments that have a help text in add_argument()"""
    pass

def parseArgs():
	"""
	parseArgs() verifies input data and converts it to optimal format.
	For files and directories: they exist (if expected to), they are absolute paths, converted to pathlib.Path
	"""
	## Read args
	parser = argparse.ArgumentParser(fromfile_prefix_chars="@",
		formatter_class=TFormatter,
		description=__doc__, epilog=__copyright__)

	# Main args
	parser.add_argument("files", nargs="*", help="HTML and MAFF files")
	parser.add_argument("--format", "-f", help="Output format, Python f-string syntax. Can run almost any Python code. See --help for using selectors (sel.h1) and specials.", default="{h1}.{ext}" )

	# Helper args
	parser.add_argument("-v", "--verbose", action="store_const", dest="log_level", const=INFO, default=WARNING, help="Set logging level to verbose (INFO)")
	parser.add_argument("-d", "--debug", action="store_const", dest="log_level", const=DEBUG)

	#parser.add_argument("-n", "--count", type=int, default=0, help="Number of records to process. Use zero (0) for unlimited.")
	parser.add_argument("--suggest", "-s", default=False, action=argparse.BooleanOptionalAction, help='''Suggest tags and metadata for files, showing both selectors "{sel.h1}" and matches "Tero's homepage".''')
	parser.add_argument("--rename", default=False, action=argparse.BooleanOptionalAction, help='''Rename files to output format.''')
	parser.add_argument("--no-action", "-n", default=False, action=argparse.BooleanOptionalAction, help='''Does not actually modify any files, but shows what would happen.''')
	args = parser.parse_args()

	## Set up logging
	if args.log_level == DEBUG:
		logformat="%(funcName)s():%(lineno)i: %(message)s %(levelname)s"
	else:
		logformat="%(message)s"
	logging.basicConfig(level=args.log_level, format=logformat)
	debug(args)

	## Validate arguments
	if not args.files:
		warning("Usage: 'hoto foo.html'. Try --help.")
	###	Turn paths to Path()
	args.paths = []
	for file in args.files:
		path = Path(file)
		if not path.is_file():
			error(f'"{path}" does not exist or is not a file! Try --help. Exiting...')
			sys.exit(1)
		args.paths.append(path)
	### Warn for likely incorrect parameters
	if not '{' in args.format:
		args.format = '{'+args.format+'}'
		info(f'''Automatically added curly brackets around your format string to make it variable. Your format string is now --format="{args.format}" ''')
		# warning(f'''Warning: Format string does not contain any variables. Variables must be surrounded by curly brackets "{{}}" aka whiskers. Correct: --format="{{sel.h1}}", prints the result of selecting h1 in HTML. Incorrect: --format="sel.h1", which prints literal text "sel.h1". Your current --format is "{args.format}".''')

	return args

### Tag and Metadata Extraction ###

class Selector():
	"""Call this class from f-string to extract HTML tags, 
	dot notation 'sel.h1' or function 'self("p:first")'
	"""

	def __init__(self, htmlStr):
		self.d = pq(htmlStr)

	def __get_selector__(self, selector, find=None, replace="", maxChars=160): 
		# own function, underscores prevent overlap with tags
		s = self.d(selector).text()
		if find:
			s = re.sub(find, replace, s) # todo: multiline
		return s.strip()[:maxChars]

	def __getattr__(self, selector, find=None, replace=""): # dot notation: sel.h1
		if "__description" == selector:
			s = self.d('meta[name="description"]').attr("content")
		elif "__keywords" == selector:
			s = self.d('meta[name="keywords"]').attr("content")
		else:
			s = self.__get_selector__(selector, find=find, replace=replace)
		if not s:
			return "" # none return value for var
		return s.strip()
		# todo: should we have first=true by default, so "h1" becomes "h1:first" ?

	def __call__(self, selector, find=None, replace=""): # function call: sel("p:first")
		return self.__get_selector__(selector, find=find, replace=replace)

class RDF(dict):
	def __init__(self, rdfStr):
		debug('''Parsing RDF from string...''')
		if not rdfStr:	
			debug('''No RDF found, empty RDF string.''')
			return None

		root = etree.fromstring(rdfStr)
		for child in root:
			for grandchild in child:
				for key in "title originalurl archivetime indexfilename".split(" "):
					if grandchild.tag.endswith("}"+key):
						val = grandchild.attrib.values()[0]
						# print(f"\t{val} - {key}")
						self[key] = val
		if "archivetime" in self:
			self.archiveDatetime = parsedate_to_datetime(self.archivetime)
			self.archived = self.archiveDatetime.strftime("%Y-%m-%d w%V %a")
			self.year = self.archiveDatetime.year
		if "originalurl" in self:
			self.host = urlparse(self.originalurl).netloc

	__getattr__ = dict.get
	__setattr__ = dict.__setitem__
	__delattr__ = dict.__delitem__

def readPath(path):
	"Read pathlib.Path path to string, optionally extracting files from inside MAFF zip"
	info(f'Reading "{path}"...')
	# verify arguments
	if not path.is_file():
		error(f'"{path}" does not exist or is not a file! Try --help. Exiting...')
		sys.exit(1)
		
	# easy plain HTML first, for early exit
	if not path.suffix in [".maff", ".zip"]:
		debug(f'''Reading plain HTML file "{path}" (suffix: "{path.suffix}") ''')
		htmlStr = path.read_text(encoding="utf-8", errors="replace")
		return htmlStr, None

	debug(f'''Reading ZIP file "{path}" ''')
	rdfStr = None
	with zipfile.ZipFile(path) as zf:
		names = zf.namelist()
		for zippedFile in  zf.namelist():
			if zippedFile.endswith("/index.rdf"):
				debug(f'''matched index.rdf: "{zippedFile}"''')
				with zf.open(zippedFile, "r") as f:
					b = f.read()
					rdfStr = b.decode("utf-8")
			if zippedFile.endswith("/index.html"):
				debug(f'''matched index.html: "{zippedFile}"''')
				with zf.open(zippedFile, "r") as f:
					b = f.read()
					htmlStr = b.decode("utf-8")
	return htmlStr, rdfStr

def filenameClean(s, keepext=None):
	if keepext and s.endswith("."+keepext):
		# debug(f'Keeping extension "{keepext}"')
		s = s.replace("."+keepext, "")
	s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore') # convert scandics to aaoAAO
	s = s.decode("ascii", "ignore")
	assert type(s) == str
	s = re.sub("[:/^\[\]\.]", "_", s)
	if keepext:
		s += "."+keepext
		debug(f'Keeping extension "{keepext}".')
	return s

### main ###

def processFile(path, args):
	info(f'## Processing file "{path}"')
	htmlStr, rdfStr = readPath(path)	

	info(f'### Extracting Tags and Metadata from "{path}"')
	sel = Selector(htmlStr)
	rdf = RDF(rdfStr)

	info(f"### Adding Convenience Variables (like title, desc...)")
	title = sel.title
	h1 = sel.h1
	ext = path.suffix.replace(".", "")
	year = rdf.year
	filename = path.name
	stem = path.stem
	archived = rdf.archived
	host = rdf.host

	if args.suggest:
		print("## ", path)
		for key in "sel.h1 sel('h1:first') sel.title sel('h2:first') sel('h1',find='Tero',replace='Someone') path path.suffix path.name rdf.nonexistingkey rdf.originalurl rdf.archived rdf.year sel.__description sel.__keywords title ext h1 year filename stem host".split(" "):
			key = key.strip()
			val = eval(key)
			if not val:
				val = "(not found)"
			print(f"{val} - {key}")
		return

	formatString = 'f"'+args.format+'"' # f"sel.h1"
	extracted = eval(formatString) # "Tero's Homepage"
	
	if not args.rename:
		print(extracted)
		return

	extracted = filenameClean(extracted, keepext=ext)
	new = path.parent.joinpath(extracted)
	if args.no_action:
		warning("Simulating only, no files will be modified. (--no-action)")
	print(f'''"{path}" ->\n \t"{new}" ''')
	if not args.no_action:
		path.rename(new)
		warning("Renamed file.")

def main():
	args=parseArgs()
	for path in args.paths:
		processFile(path, args)

if __name__ == "__main__":
	main()

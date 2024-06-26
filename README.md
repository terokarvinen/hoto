# hoto - HTML and MAFF tag extraction

Would you like to have nice names for your stored web pages? [Install](#install), [Quickstart](#quickstart)

Extract HTML tags and metadata, optionally rename files. Supports MAFF as used by WebScrapbook. 

Features

- Extract HTML tags
	- h1
	- title
	- .authorname
- Rename HTML and MAFF files using HTML tags and metadata
- Use CSS selectors, just like jQuery
	- Uses [PyQuery library](https://pyquery.readthedocs.io/en/stable/index.html), and supports PyQuery extra features
- Extract MAFF files
	- Supports [MAFF (Mozilla Archive Format)](https://www.amadzone.org/mozilla-archive-format/maff-specification.html) archives created by [WebScrapbook Firefox addon](https://github.com/danny0838/webscrapbook) ([install](https://addons.mozilla.org/en-US/firefox/addon/webscrapbook/))
	- Supports index.rdf metadata
		- archive date - automatically converted to [calendar.txt format](https://terokarvinen.com/2024/format-date-calendar-txt/) (2024-06-15 w24 Sat)
		- original host
	- Transparently extracts HTML and RDF from compressed MAFF
- Run almost any Python code when renaming (using f-string format)
- Replace HTML tag content with regular expressions
- Automatically process large number of files

## Quickstart

	$ wget terokarvinen.com
	...'index.html' saved

	$ ./hoto.py index.html
	Tero Karvinen.html

	$ ./hoto.py index.html --suggest|grep -v "not found"
	##  index.html
	Tero Karvinen - sel.h1
	Tero Karvinen - sel('h1:first')
	Tero Karvinen - Learn Free software with me - sel.title
	Python weppipalvelu - ideasta tuotantoon - sel('h2:first')
	Someone Karvinen - sel('h1',find='Tero',replace='Someone')
	index.html - path
	.html - path.suffix
	index.html - path.name
	Build your own robots, hack computers (legally) and admin Linux boxes - hundreds of them! - sel.__description
	Tero Karvinen - Learn Free software with me - title
	html - ext
	Tero Karvinen - h1
	index.html - filename
	index - stem

	$ ./hoto.py index.html --rename
	$ ls
	hoto.py  'Tero Karvinen.html'

## Install

It's a single Python script, so you can just run it. 

	$ sudo apt-get update
	$ sudo apt-get install wget python3-pyquery python3-rdflib
	$ wget https://raw.githubusercontent.com/terokarvinen/hoto/main/hoto.py
	$ chmod ugo+x hoto.py
	$ ./hoto.py
	Usage: 'hoto foo.html'. Try --help.

## hoto --help

	usage: hoto.py [-h] [--format FORMAT] [-v] [-d]
	               [--suggest | --no-suggest | -s] [--rename | --no-rename]
	               [--no-action | --no-no-action | -n]
	               [files ...]

hoto - rename HTML and MAFF files from HTML tags and metadata

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

See you at https://TeroKarvinen.com

	positional arguments:
	  files                 HTML and MAFF files (default: None)

	options:
	  -h, --help            show this help message and exit
	  --format FORMAT, -f FORMAT
	                        Output format, Python f-string syntax. Can run almost
	                        any Python code. See --help for using selectors
	                        (sel.h1) and specials. (default: {h1}.{ext})
	  -v, --verbose         Set logging level to verbose (INFO) (default: 30)
	  -d, --debug
	  --suggest, --no-suggest, -s
	                        Suggest tags and metadata for files, showing both
	                        selectors "{sel.h1}" and matches "Tero's homepage".
	                        (default: False)
	  --rename, --no-rename
	                        Rename files to output format. (default: False)
	  --no-action, --no-no-action, -n
	                        Does not actually modify any files, but shows what
	                        would happen. (default: False)

Copyright 2024 Tero Karvinen https://TeroKarvinen.com

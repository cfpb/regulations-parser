Regulations Parser
==================

[![Build Status](https://travis-ci.org/eregs/regulations-parser.png)](https://travis-ci.org/eregs/regulations-parser)

Parse a regulation (plain text) into a well-formated JSON tree (along with
associated layers, such as links and definitions). This works hand-in-hand
with regulations-site, a front-end for the data structures generated.

## Features

* Split regulation into paragraph-level chunks
* Create a tree which defines the hierarchical relationship between these
chunks
* Layer for external citations -- links to Acts, Public Law, etc.
* Layer for graphics -- converting image references into federal register
urls
* Layer for internal citations -- links between parts of this regulation
* Layer for interpretations -- connecting regulation text to the
interpretations associated with it
* Layer for key terms -- pseudo headers for certain paragraphs
* Layer for meta info -- custom data (some pulled from federal notices)
* Layer for paragraph markers -- specifying where the initial paragraph
marker begins and ends for each paragraph
* Layer for section-by-section analysis -- associated analyses (from FR
notices) with the text they are analyzing
* Layer for table of contents -- a listing of headers
* Layer for terms -- defined terms, including their scope

## Requirements

* lxml (3.2.0) - Used to parse out information XML from the federal register
* pyparsing (1.5.7) - Used to do generic parsing on the plain text
* inflection (0.1.2) - Helps determine pluralization (for terms layer)
* requests (1.2.3) - Client library for writing output to an API

## API Docs

[Read The Docs](https://regulation-parser.readthedocs.org/en/latest/)

## Installation

### Getting the Code and Development Libs

Download the source code from GitHub (e.g. ```git clone [URL]```)

Make sure the ```libxml``` libraries are present. On Ubuntu/Debian, install
it via

```bash
$ sudo apt-get install libxml2-dev libxslt-dev
```

### Create a virtual environment (optional)

```bash
$ sudo pip install virtualenvwrapper
$ mkvirtualenv parser
```

### Get the required libraries

```bash
$ cd regulations-parser
$ pip install -r requirements.txt
```

### Pull down the regulation text

At the moment, we parse from a plain-text version of the regulation. This
requires such a plain text version exist. One of the easiest ways to do that
is to find your full regulation from
[e-CFR](http://www.ecfr.gov/cgi-bin/ECFR?page=browse). For example, CFPB's
[regulation
E](http://www.ecfr.gov/cgi-bin/text-idx?c=ecfr&rgn=div5&view=text&node=12:8.0.2.9.4&idno=12).

Once you have your regulation, copy-paste from "Part" to the "Back to Top"
link at the bottom of the regulation. Next, we need to get rid of some of
the non-helpful info e-CFR puts in. Delete lines of the form

* ^Link to an amendment .*$
* Back to Top

Also, delete any table of contents which contain the section character.

Save that file as a text file (e.g. reg.txt).

### Run the parser

The syntax is 

```bash
$ python build_from.py regulation.txt title doc_#/version act_title
act_section
```

So, for the regulation we copy-pasted above, we could run
```bash
$ python build_from.py reg.txt 12 `date +"%Y%m%d"` 15 1693
```

This will generate three folders, ```regulation```, ```notice```, and
```layer``` in the ```OUTPUT_DIR``` (current directory by default).

### Settings

All of the settings listed in ```settings.py``` can be overridden in a
```local_settings.py``` file. Current settings include:

* ```OUTPUT_DIR``` - a string with the path where the output files should be
written. Only useful if the JSON files are to be written to disk.
* ```API_BASE``` - a string defining the url root of an API (if the output
files are to be written to an API instead)
* ```META``` - a dictionary of extra info which will be included in the
"meta" layer. Useful fields include "contact_info" (an html string),
"effective" (a dictionary with "url":string, "title":string,
"date":date-string), and "last_notice" (a dictionary with "url":string,
"title":string, "action":string, "published":date-string,
"effective":date-string)
* ```SUBPART_STARTS``` - a dictionary describing when subparts begin. See
```settings.py``` for an example.
* ```CFR_TITLE``` - array of CFR Title names (used in the meta layer)
* ```DEFAULT_IMAGE_URL``` - string format used in the graphics layer
* ```IMAGE_OVERRIDES``` - a dictionary between specific image ids and unique
urls for them

### Keyterms Layer
@TODO


### Building the documentation

For most tweaks, you will simply need to run the Sphinx documentation
builder again.

```
$ pip install Sphinx
$ cd docs
$ make dirhtml
```

The output will be in ``docs/_build/dirhtml```.

If you are adding new modules, you may need to re-run the skeleton build
script first:

```
$ pip install Sphinx
$ sphinx-apidoc -F -o docs regparser/
```


##  Running Tests

To run the unit tests, make sure you have added all of the testing
requirements:

```bash
$ pip install -r requirements_test.txt
```

Then, run nose on all of the available unit tests:

```bash
$ nosetests tests/*.py
```

If you'd like a report of test coverage, use the [nose-cov](https://pypi.python.org/pypi/nose-cov) plugin:

```bash
$ nosetests --with-cov --cov-report term-missing --cov regparser tests/*.py
```

Regulations Parser
==================

[![Build Status](https://travis-ci.org/cfpb/regulations-parser.png)](https://travis-ci.org/cfpb/regulations-parser)
[![Coverage Status](https://coveralls.io/repos/cfpb/regulations-parser/badge.png)](https://coveralls.io/r/cfpb/regulations-parser)

Parse a regulation (plain text) into a well-formated JSON tree (along with
associated layers, such as links and definitions) with this tool. It also
pulls in notice content from the Federal Register and creates JSON
representations for them. The parser works hand-in-hand with
regulations-site, a front-end for the data structures generated, and
regulations-core, an API for hosting the data.

This repository is part of a larger project. To read about it, please see 
[http://eregs.github.io/eregulations/](http://eregs.github.io/eregulations/).

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
* Create diffs between versions of the regulations (if those versions are
  available from an API)

## Requirements

* lxml (3.2.0) - Used to parse out information XML from the federal register
* pyparsing (1.5.7) - Used to do generic parsing on the plain text
* inflection (0.1.2) - Helps determine pluralization (for terms layer)
* requests (1.2.3) - Client library for writing output to an API

If running tests:

* nose (1.2.1) - A pluggable test runner
* mock (1.0.1) - Makes constructing mock objects/functions easy
* coverage (3.6) - Reports on test coverage
* cov-core (1.7) - Needed by coverage
* nose-cov (1.6) - Connects nose to coverage

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

We've also found that tables of contents can cause random issues with the
parser, so we recommend removing them. The parser will most likely generate
the same content in a layer.

Save that file as a text file (e.g. reg.txt).

### Run the parser

The syntax is 

```bash
$ python build_from.py regulation.txt title notice_doc_# act_title act_section
```

So, for the regulation we copy-pasted above, we could run
```bash
$ python build_from.py reg.txt 12 2013-06861 15 1693
```

Here ```12``` is the CFR title number (in our case, for "Banks and
Banking"), ```2013-06861``` is the last notice used to create this version
(i.e. the last "final rule" which is currently in effect), ```15``` is the
title of "the Act" and ```1693``` is the relevant section. Wherever the
phrase "the Act" is used in the regulation, the external link parser will
treat it as "15 U.S.C. 1693".  The final rule number is used to pull in
section-by-section analyses and deduce which notices were used to create
this version of the regulation. To find this, use the 
[Federal Register](https://www.federalregister.gov/), finding the last,
effective final rule for your version of the regulation and copying the
document number from the meta data (currently in a table on the right side).

This will generate four folders, ```regulation```, ```notice```, ``layer``
and possibly ``diff`` in the ```OUTPUT_DIR``` (current directory by default).

If you'd like to write the data to an api instead (most likely, one running
regulations-core), you can set the ```API_BASE``` setting (described below).

### Settings

All of the settings listed in ```settings.py``` can be overridden in a
```local_settings.py``` file. Current settings include:

* ```OUTPUT_DIR``` - a string with the path where the output files should be
  written. Only useful if the JSON files are to be written to disk.
* ```API_BASE``` - a string defining the url root of an API (if the output
  files are to be written to an API instead)
* ```META``` - a dictionary of extra info which will be included in the
  "meta" layer. This is free-form.
* ```CFR_TITLE``` - array of CFR Title names (used in the meta layer); not
  required as those provided are current
* ```DEFAULT_IMAGE_URL``` - string format used in the graphics layer; not
  required as the default should be adequate 
* ```IMAGE_OVERRIDES``` - a dictionary between specific image ids and unique
  urls for them -- useful if the Federal Register versions aren't pretty

### Keyterms Layer

Unlike our other layers (at the moment), the Keyterms layer (which indicates
pseudo titles used as headers in regulation paragraphs) is built using XML
from the Federal Register rather than plain text. Right now, this is a
particularly manual process which involves manually retrieving each notice's
XML, generating a layer, and merging the results with the existing layer.
This is not a problem if the regulation is completely re-issued.

In any event, to generate the layer based on a particular XML, first
download that XML (found by on [federalregister.gov](https://www.federalregister.gov) 
by selecting 'DEV', then 'XML' on a notice). Then, modify the
```build_tree.py``` file to point to the correct XML. Running this script
will convert the XML into a JSON tree, maintaining some tags that the plain
text version does not.

Save this JSON to ```/tmp/xtree.json```, then run ```generate_layers.py```.
The output *should* be a complete layer; so combine information from
multiple rules, simply copy-paste the fields of the newly generated layer.

An alternative (or additional option) is to use the
```plaintext_keyterms.py``` script, which adds best-guesses for the
keyterms. If you do not have the ```/tmp/xtree.json``` from before, create a
file with ```{}``` in its place. Modify ```plaintext_keyterms.py``` so that
the ```api_stub.get_regulation_as_json``` line uses the regulation output of
```build_from.py``` as described above. Running ```plaintext_keyterms.py```
will generate a keyterm layer.

### Graphics Layer

For obvious reasons, plain text does not include images, but we would still
like to represent model forms and the like. We use Markdown style image
inclusion in the plaintext:

```
![Appendix A9](ER27DE11.000)
```

This will be converted to an img tag by the graphics layer, pointing to the
image as included in the Federal Register. Note that you can override each
image via the ```IMAGE_OVERRIDES``` setting (see above).

### Building the documentation

For most tweaks, you will simply need to run the Sphinx documentation
builder again.

```
$ pip install Sphinx
$ cd docs
$ make dirhtml
```

The output will be in ```docs/_build/dirhtml```.

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

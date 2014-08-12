Regulations Parser
==================

[![Build Status](https://travis-ci.org/cfpb/regulations-parser.png)](https://travis-ci.org/cfpb/regulations-parser)
[![Coverage Status](https://coveralls.io/repos/cfpb/regulations-parser/badge.png)](https://coveralls.io/r/cfpb/regulations-parser)

This library/tool parses federal regulations (either plain text or XML) and
much of their associated content. It can write the results to JSON files, an
API, or even a git repository. The parser works hand-in-hand with
regulations-core, and API for hosting the parsed regulations and
regulation-site, a front-end for the data structures generated.

This repository is part of a larger project. To read about it, please see 
[http://cfpb.github.io/eRegulations/](http://cfpb.github.io/eRegulations/).

## Quick Start

Here's an example, using CFPB's regulation H.

1. `git clone https://github.com/cfpb/regulations-parser.git`
1. `cd regulations-parser`
1. `pip install -r requirements.txt`
1. `wget
   http://www.gpo.gov/fdsys/pkg/CFR-2012-title12-vol8/xml/CFR-2012-title12-vol8-part1004.xml`
1. `python build_from.py CFR-2012-title12-vol8-part1004.xml 12 2011-18676 15
   1693`

At the end, you will have new directories for `regulation`, `layer`,
`diff`, and `notice` which would mirror the JSON files sent to the API.

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
* Layer for additional formatting, including tables, "notes", code blocks,
  and subscripts
* Build whole versions of the regulation from the changes found in final
  rules
* Create diffs between these versions of the regulations

## Requirements

* lxml (3.2.0) - Used to parse out information XML from the federal register
* pyparsing (1.5.7) - Used to do generic parsing on the plain text
* inflection (0.1.2) - Helps determine pluralization (for terms layer)
* requests (1.2.3) - Client library for writing output to an API
* requests_cache (0.4.4) - *Optional* - Library for caching request results
  (speeds up rebuilding regulations)
* GitPython (0.3.2.RC1) - Allows the regulation to be written as a git repo
* python-constraint (1.2) - Used to determine paragraph depth

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

The parser can generally read either plain-text or XML versions of a
regulation, though the XML version gives much better hints. If you have a
regulation as plain text, make sure to remove any table-of-contents and
superflous lines (e.g. "Link to an amendment" and "Back to Top", which might
appear if copy-pasting from
[e-CFR](http://www.ecfr.gov/cgi-bin/ECFR?page=browse).

A better strategy would be to parse using an XML file. This XML can come
from [annual editions](http://www.gpo.gov/fdsys/browse/collectionCfr.action)
of the regulations, or Federal Register notices, if the notice contains a
reissuance of the whole regulation (e.g. CFPB
[re-issued](https://www.federalregister.gov/articles/xml/201/131/725.xml)
regulation E).


### Run the parser

The syntax is 

```bash
$ python build_from.py regulation.ext title notice_doc_# act_title act_section
```

For example, to match the reissuance above:
```bash
$ python build_from.py 725.xml 12 2013-1725 15 1693
```

Here ```12``` is the CFR title number (in our case, for "Banks and
Banking"), ```2013-1725``` is the last notice used to create this version
(i.e. the last "final rule" which is currently in effect), ```15``` is the
title of "the Act" and ```1693``` is the relevant section. Wherever the
phrase "the Act" is used in the regulation, the external link parser will
treat it as "15 U.S.C. 1693".  The final rule number is used to pull in
section-by-section analyses and deduce which notices were used to create
this version of the regulation. It also helps determine which notices to use
when building additional versions of the regulation. To find the document
number, use the [Federal Register](https://www.federalregister.gov/),
finding the last, effective final rule for your version of the regulation
and copying the document number from the meta data (currently in a table on
the right side).

Running the command will generate four folders, ```regulation```,
```notice```, ``layer`` and possibly ``diff`` in the ```OUTPUT_DIR```
(current directory by default).

If you'd like to write the data to an api instead (most likely, one running
regulations-core), you can set the ```API_BASE``` setting (described below).

### Settings

All of the settings listed in ```settings.py``` can be overridden in a
```local_settings.py``` file. Current settings include:

* ```OUTPUT_DIR``` - a string with the path where the output files should be
  written. Only useful if the JSON files are to be written to disk.
* ```API_BASE``` - a string defining the url root of an API (if the output
  files are to be written to an API instead)
* ```GIT_OUTPUT_DIR``` - a string path which will be used to initialize a
  git repository when writing history
* ```META``` - a dictionary of extra info which will be included in the
  "meta" layer. This is free-form, but could be used for copyright
  information, attributions, etc.
* ```CFR_TITLES``` - array of CFR Title names (used in the meta layer); not
  required as those provided are current
* ```DEFAULT_IMAGE_URL``` - string format used in the graphics layer; not
  required as the default should be adequate 
* ```IGNORE_DEFINITIONS_IN``` - a dictionary mapping CFR part numbers to a
  list of terms that should *not* contain definitions. For example, if
  'state' is a defined term, it may be useful to exclude the phrase 'shall
  state'. Terms associated with the constant, `ALL`, will be ignored in all
  CFR parts parsed.
* ```OVERRIDES_SOURCES``` - a list of python modules (represented via
  string) which should be consulted when determining image urls. Useful if
  the Federal Register versions aren't pretty. Defaults to a `regcontent`
  module.
* ```MACRO_SOURCES``` - a list of python modules (represented via strings)
  which should be consulted if replacing chunks of XML in notices. This is
  more or less deprecated by `LOCAL_XML_PATHS`. Defaults to a `regcontent`
  module.
* ```REGPATCHES_SOURCES``` - a list of python modules (represented via
  strings) which should be consulted when determining changes to regulations
  made in final rules.  Defaults to a `regcontent` module
* ```LOCAL_XML_PATHS``` - a list of paths to search for notices from the
  Federal Register. This directory should match the folder structure of the
  Federal Register. If a notice is present in one of the local paths, that
  file will be used instead of retrieving the file, allowing for local
  edits, etc. to help the parser.

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

## Building the documentation

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

## Additional Details

### build_from flow

### output types

### patches, etc.

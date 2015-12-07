# -*- coding: utf-8 -*-

import json
import os
import shutil
import tempfile
from unittest import TestCase

# Some Python 3-friendly imports
try:
    import builtins
except ImportError:
    import __builtin__ as builtins

from mock import patch
import lxml.etree as etree

from regparser.api_writer import (
    APIWriteContent, Client, FSWriteContent, GitWriteContent, Repo, 
    XMLWriteContent)
from regparser.tree.struct import Node
from regparser.notice.diff import Amendment, DesignateAmendment
import settings


class FSWriteContentTest(TestCase):
    def setUp(self):
        settings.OUTPUT_DIR = tempfile.mkdtemp() + '/'

    def tearDown(self):
        shutil.rmtree(settings.OUTPUT_DIR)
        settings.OUTPUT_DIR = ''

    def test_write_new_dir(self):
        writer = FSWriteContent("a/path/to/something")
        writer.write({"testing": ["body", 1, 2]})

        wrote = json.loads(open(settings.OUTPUT_DIR
                                + '/a/path/to/something').read())
        self.assertEqual(wrote, {'testing': ['body', 1, 2]})

    def test_write_existing_dir(self):
        os.mkdir(settings.OUTPUT_DIR + 'existing')
        writer = FSWriteContent("existing/thing")
        writer.write({"testing": ["body", 1, 2]})

        wrote = json.loads(open(settings.OUTPUT_DIR
                                + '/existing/thing').read())
        self.assertEqual(wrote, {'testing': ['body', 1, 2]})

    def test_write_overwrite(self):
        writer = FSWriteContent("replace/it")
        writer.write({"testing": ["body", 1, 2]})

        writer = FSWriteContent("replace/it")
        writer.write({"key": "value"})

        wrote = json.loads(open(settings.OUTPUT_DIR + '/replace/it').read())
        self.assertEqual(wrote, {'key': 'value'})

    def test_write_encoding(self):
        writer = FSWriteContent("replace/it")
        writer.write()

        wrote = json.loads(open(settings.OUTPUT_DIR + '/replace/it').read())
        self.assertEqual(wrote['text'], 'Content')

        writer.write(Amendment("action", "label"))
        wrote = json.loads(open(settings.OUTPUT_DIR + '/replace/it').read())
        self.assertEqual(wrote, ['action', ['label']])

        writer.write(Amendment("action", "label", 'destination'))
        wrote = json.loads(open(settings.OUTPUT_DIR + '/replace/it').read())
        self.assertEqual(wrote, ['action', ['label'], 'destination'])

        writer.write(DesignateAmendment("action", ["label"], 'destination'))
        wrote = json.loads(open(settings.OUTPUT_DIR + '/replace/it').read())
        self.assertEqual(wrote, ['action', [['label']], 'destination'])


class APIWriteContentTest(TestCase):

    def setUp(self):
        self.base = settings.API_BASE
        settings.API_BASE = 'http://example.com/'

    def tearDown(self):
        settings.API_BASE = self.base

    @patch('regparser.api_writer.requests')
    def test_write(self, requests):
        writer = APIWriteContent("a/path")
        data = {"testing": ["body", 1, 2]}
        writer.write(data)

        args, kwargs = requests.post.call_args
        self.assertEqual("http://example.com/a/path", args[0])
        self.assertTrue('headers' in kwargs)
        self.assertTrue('content-type' in kwargs['headers'])
        self.assertEqual('application/json',
                         kwargs['headers']['content-type'])
        self.assertTrue('data' in kwargs)
        self.assertEqual(data, json.loads(kwargs['data']))


class GitWriteContentTest(TestCase):
    def setUp(self):
        self.had_output = hasattr(settings, 'GIT_OUTPUT_DIR')
        self.old_output = getattr(settings, 'GIT_OUTPUT_DIR', '')
        settings.GIT_OUTPUT_DIR = tempfile.mkdtemp() + '/'

    def tearDown(self):
        shutil.rmtree(settings.GIT_OUTPUT_DIR)
        if self.had_output:
            settings.GIT_OUTPUT_DIR = self.old_output
        else:
            del(settings.GIT_OUTPUT_DIR)

    def test_write(self):
        """Integration test."""
        p3a = Node('(a) Par a', label=['1111', '3', 'a'])
        p3b = Node('(b) Par b', label=['1111', '3', 'b'])
        p3 = Node('Things like: ', label=['1111', '3'], title='Section 3',
                  children=[p3a, p3b])
        sub = Node('', label=['1111', 'Subpart', 'E'], title='Subpart E',
                   node_type=Node.SUBPART, children=[p3])
        a3a = Node('Appendix A-3(a)', label=['1111', 'A', '3(a)'],
                   title='A-3(a) - Some Title', node_type=Node.APPENDIX)
        app = Node('', label=['1111', 'A'], title='Appendix A',
                   node_type=Node.APPENDIX, children=[a3a])
        i3a1 = Node('1. P1', label=['1111', '3', 'a', 'Interp', '1'],
                    node_type=Node.INTERP)
        i3a = Node('', label=['1111', '3', 'a', 'Interp'],
                   node_type=Node.INTERP, children=[i3a1],
                   title='Paragraph 3(a)')
        i31 = Node('1. Section 3', label=['1111', '3', 'Interp', '1'],
                   node_type=Node.INTERP)
        i3 = Node('', label=['1111', '3', 'Interp'], node_type=Node.INTERP,
                  title='Section 1111.3', children=[i3a, i31])
        i = Node('', label=['1111', 'Interp'], node_type=Node.INTERP,
                 title='Supplement I', children=[i3])
        tree = Node('Root text', label=['1111'], title='Regulation Joe',
                    children=[sub, app, i])

        writer = GitWriteContent("/regulation/1111/v1v1")
        writer.write(tree)

        dir_path = settings.GIT_OUTPUT_DIR + "regulation" + os.path.sep
        dir_path += '1111' + os.path.sep

        self.assertTrue(os.path.exists(dir_path + '.git'))
        dirs, files = [], []
        for dirname, child_dirs, filenames in os.walk(dir_path):
            if ".git" not in dirname:
                dirs.extend(os.path.join(dirname, c) for c in child_dirs
                            if c != '.git')
                files.extend(os.path.join(dirname, f) for f in filenames)
        for path in (('Subpart-E',), ('Subpart-E', '3'),
                     ('Subpart-E', '3', 'a'), ('Subpart-E', '3', 'b'),
                     ('A',), ('A', '3(a)'),
                     ('Interp',), ('Interp', '3-Interp'),
                     ('Interp', '3-Interp', '1'),
                     ('Interp', '3-Interp', 'a-Interp'),
                     ('Interp', '3-Interp', 'a-Interp', '1')):
            path = dir_path + os.path.join(*path)
            self.assertTrue(path in dirs)
            self.assertTrue(path + os.path.sep + 'index.md' in files)

        p3c = p3b
        p3c.text = '(c) Moved!'
        p3c.label = ['1111', '3', 'c']

        writer = GitWriteContent("/regulation/1111/v2v2")
        writer.write(tree)

        dir_path = settings.GIT_OUTPUT_DIR + "regulation" + os.path.sep
        dir_path += '1111' + os.path.sep

        self.assertTrue(os.path.exists(dir_path + '.git'))
        dirs, files = [], []
        for dirname, child_dirs, filenames in os.walk(dir_path):
            if ".git" not in dirname:
                dirs.extend(os.path.join(dirname, c) for c in child_dirs
                            if c != '.git')
                files.extend(os.path.join(dirname, f) for f in filenames)
        for path in (('Subpart-E',), ('Subpart-E', '3'),
                     ('Subpart-E', '3', 'a'), ('Subpart-E', '3', 'c'),
                     ('A',), ('A', '3(a)'),
                     ('Interp',), ('Interp', '3-Interp'),
                     ('Interp', '3-Interp', '1'),
                     ('Interp', '3-Interp', 'a-Interp'),
                     ('Interp', '3-Interp', 'a-Interp', '1')):
            path = dir_path + os.path.join(*path)
            self.assertTrue(path in dirs)
            self.assertTrue(path + os.path.sep + 'index.md' in files)
        self.assertFalse(dir_path + os.path.join('Subpart-E', '3', 'b')
                         in dirs)

        commit = Repo(dir_path).head.commit
        self.assertTrue('v2v2' in commit.message)
        self.assertEqual(1, len(commit.parents))
        commit = commit.parents[0]
        self.assertTrue('v1v1' in commit.message)
        self.assertEqual(1, len(commit.parents))
        commit = commit.parents[0]
        self.assertTrue('1111' in commit.message)
        self.assertEqual(0, len(commit.parents))


class XMLWriteContentTestCase(TestCase):

    def setUp(self):
        settings.OUTPUT_DIR = tempfile.mkdtemp() + '/'

    @patch.object(builtins, 'open')
    def test_write(self, mock_open):
        layers = {'terms': {'referenced': {}},}
        # writer = XMLWriteContent("a/path", layers=layers, notices={})
        # writer.write(Node("Content", label="1000"))
        # print mock_open.call_args
        # print args, kwargs
        
    def test_write_notice(self):
        # XXX: There's nothing to test here (yet?)
        pass

    def test_extract_definitions(self):
        layers = {
            'terms': {'referenced': {
                u'my defined term:1000-1-a': {
                    'position': (0, 15),
                    'term': u'my defined term',
                    'reference': '1000-1-a',
                },
            }},
        }
        expected_definitions = {'1000-1-a': 
            {'term': u'my defined term', 'offset': (0, 15)}}

        # extract_definitions is called in __init__ to create 
        # layers['definitions'] 
        writer = XMLWriteContent("a/path", '2015-12345', 
                                 layers=layers, notices={})
        self.assertEqual(expected_definitions, 
                         writer.layers['definitions'])

    def test_apply_terms(self):
        text="my defined term is my favorite of all the defined term" \
             "because it is mine"
        replacements = [{
            'ref': u'my defined term:1000-1-a',
            'offsets': [(0, 15)]
        },]
        expected_result = ([(0, 15)], 
            ['<ref target="1000-1-a" reftype="term">my defined term</ref>'])
        result = XMLWriteContent.apply_terms(text, replacements)
        self.assertEqual(expected_result, result)

    def test_apply_paragraph_markers(self):
        text = "(a) This is a paragraph with a marker"
        replacements = [{'text': u'(a)', 'locations': [0]}]
        expected_result = ([[0, 3]], [''])
        result = XMLWriteContent.apply_paragraph_markers(text, replacements)
        self.assertEqual(expected_result, result)

    def test_apply_internal_citations(self):
        text = "Now I'm going to cite 1000.1 right here."
        replacements = [{'citation': [u'1000', u'1'], 
                         'offsets': [(22, 28)]}]
        expected_result = ([(22, 28)], 
            ['<ref target="1000-1" reftype="internal">1000.1</ref>'])
        result = XMLWriteContent.apply_internal_citations(text, replacements)
        self.assertEqual(expected_result, result)
    
    def test_apply_external_citations(self):
        text = "Pub. L. 111-203, 124 Stat. 1376"
        replacements = [{'citation': [u'124', 'Stat.', u'1376'], 
                         'citation_type': 'STATUTES_AT_LARGE', 
                         'offsets': [[17, 31]]},]
        expected_result = ([[17, 31]], 
                ['<ref target="STATUTES_AT_LARGE:124-Stat.-1376" '
                 'reftype="external">124 Stat. 1376</ref>'])
        result = XMLWriteContent.apply_external_citations(text, replacements)
        self.assertEqual(expected_result, result)

    def test_apply_definitions(self):
        text="my defined term is my favorite of all the defined term" \
             "because it is mine"
        replacement = {
            'term': u'my defined term',
            'offset': (0, 15)
        }
        expected_result = ([(0, 15)], 
                ['<def term="my defined term" '
                 'id="5bd44682146382a20d2ac0b5c1143b0ab273e8f8">'
                 'my defined term</def>'])
        result = XMLWriteContent.apply_definitions(text, replacement)
        self.assertEqual(expected_result, result)

    def test_apply_graphics(self):
        # XXX: This needs to be implemented
        self.assertTrue(False)

    def test_apply_keyterms(self):
        # XXX: The actual class method needs to be implemented.
        pass

    def test_apply_formatting(self):
        # Test a table
        replacements = [{
            'text': '|Header row|\n|---|\n||', 
            'locations': [0], 
            'table_data': {'header': [[{'text': 'Header row', 
                                        'rowspan': 1, 
                                        'colspan': 1},]], 
                           'rows': [['', '']]},
        }]
        expected_result = ([[0, 155]], 
                ['<table><header><columnHeaderRow><column colspan="1" '
                 'rowspan="1">Header row</column></columnHeaderRow>'
                 '</header><row><cell></cell><cell></cell></row></table>'])
        result = XMLWriteContent.apply_formatting(replacements)
        self.assertEqual(expected_result, result)

        # Test dashes
        replacements = [{'text': u'Model form field_____', 
                         'dash_data': {'text': u'Model form field'},
                         'locations': [0]}]
        expected_result = ([[0, 23]], [u'Model form field<dash/>'])
        result = XMLWriteContent.apply_formatting(replacements)
        self.assertEqual(expected_result, result)

        # Test fences
        # XXX: Actual fences need to be implemented
        replacements = [{
            'fence_data': {
                'lines': ['Note:', 'Some note content right here.'], 
                'type': 'note'
            }, 
            'locations': [0],
            'text': '```note\nNote:\nSome note content right here.\n```'
        }]
        # expected_result = 
        result = XMLWriteContent.apply_formatting(replacements)
        # self.assertEqual(expected_result, result)
        self.assertTrue(False)

        # Test subscripts
        # XXX: Actual subscripts need to be implemented
        replacements = [{
            'locations': [0], 
            'subscript_data': {
                "subscript": 'n', 
                'variable': 'Val'
            }, 
            'text': 'Val_{n}'
        }]
        # expected_result = 
        result = XMLWriteContent.apply_formatting(replacements)
        # self.assertEqual(expected_result, result)
        self.assertTrue(False)

    def test_add_analyses(self):
        """ Test that we can add analysis with sections within the
            primary section and footnotes. """
        text = 'This is some text that will be analyzed.'
        layers = {
            'terms': {'referenced': {}},
            'analyses': {
                '1234-1': [{
                    'publication_date': u'2015-11-17', 
                    'reference': (u'2015-12345', u'1234-1')
                }]
            }
        }
        notices = [{
            'document_number': '2015-12345',
            'section_by_section': [{
                'title': 'Section 1234.1',
                'labels': ['1234-1'], 
                'paragraphs': [
                    'This paragraph is in the top-level section.',
                ], 
                'footnote_refs': [], 
                'children': [{
                    'children': [], 
                    'footnote_refs': [
                        {
                            'offset': 16, 
                            'paragraph': 0, 
                            'reference': '1'
                        },
                        {
                            'offset': 31, 
                            'paragraph': 0, 
                            'reference': '2'
                        },
                    ],
                    'paragraphs': [
                        'I am a paragraph in an analysis section, love me!', 
                    ], 
                    'title': '(a) Section of the Analysis'
                }],
            }],
            'footnotes': {
                '1': 'Paragraphs contain text.',
                '2': 'Analysis analyzes things.'
            },
        }]
        elm = etree.Element('section')
        elm.set('label', '1234-1')
        writer = XMLWriteContent("a/path", '2015-12345', 
                                 layers=layers, notices=notices)
        writer.add_analyses(elm)

        self.assertEqual(1, len(elm.xpath('./analysis')))
        self.assertEqual(1,
            len(elm.xpath('./analysis/analysisSection')))
        self.assertEqual(1, 
            len(elm.xpath('./analysis/analysisSection/title')))
        self.assertEqual('Section 1234.1',
            elm.xpath('./analysis/analysisSection/title')[0].text)

        self.assertEqual(1,
            len(elm.xpath('./analysis/analysisSection/analysisParagraph')))
        self.assertTrue('top-level section' in 
            elm.xpath('./analysis/analysisSection/analysisParagraph')[0].text)

        self.assertEqual(1,
            len(elm.xpath('./analysis/analysisSection/analysisSection')))
        self.assertEqual(1, 
            len(elm.xpath('./analysis/analysisSection/analysisSection/title')))
        self.assertEqual('(a) Section of the Analysis',
            elm.xpath('./analysis/analysisSection/analysisSection/title')[0].text)

        self.assertEqual(1,
            len(elm.xpath('./analysis/analysisSection/analysisSection/analysisParagraph')))
        self.assertTrue('I am a paragraph' in 
            elm.xpath('./analysis/analysisSection/analysisSection/analysisParagraph')[0].text)

        self.assertEqual(2,
            len(elm.xpath('./analysis/analysisSection/analysisSection/analysisParagraph/footnote')))

    def test_fdsys(self):
        layers = {
            'terms': {'referenced': {}},
            'meta': {
                '1000': [{
                    'cfr_title_number': 12, 
                    'effective_date': u'2015-01-01', 
                    'reg_letter': u'D', 
                    'cfr_title_text': 'Banks and Banking', 
                    'statutory_name': u'TEST REGULATIONS FOR TESTING'
                }]
            }
        }
        writer = XMLWriteContent("a/path", '2015-12345', 
                                 layers=layers, notices={})
        expected_result = etree.fromstring('''
            <fdsys>
              <cfrTitleNum>12</cfrTitleNum>
              <cfrTitleText>Banks and Banking</cfrTitleText>
              <volume>8</volume>
              <date>2015-01-01</date>
              <originalDate>2015-01-01</originalDate>
              <title>TEST REGULATIONS FOR TESTING</title>
            </fdsys>
        ''', etree.XMLParser(remove_blank_text=True))
        result = writer.fdsys('1000', date='2015-01-01', orig_date='2015-01-01')
        self.assertEqual(etree.tostring(expected_result),
                etree.tostring(result))

    def test_preamble(self):
        layers = {
            'terms': {'referenced': {}},
            'meta': {
                '1000': [{
                    'cfr_title_number': 12, 
                    'effective_date': u'2015-01-01', 
                    'reg_letter': u'D', 
                    'cfr_title_text': 'Banks and Banking', 
                    'statutory_name': u'TEST REGULATIONS FOR TESTING'
                }]
            }
        }
        writer = XMLWriteContent("a/path", '2015-12345', 
                                 layers=layers, notices={})
        expected_result = etree.fromstring('''
            <preamble>
              <agency>Bureau of Consumer Financial Protection</agency>
              <cfr>
                <title>12</title>
                <section>1000</section>
              </cfr>
              <documentNumber>2015-12345</documentNumber>
              <effectiveDate>2015-01-01</effectiveDate>
            </preamble>
        ''', etree.XMLParser(remove_blank_text=True))
        result = writer.preamble('1000')
        self.assertEqual(etree.tostring(expected_result),
                etree.tostring(result))

    def test_toc_to_xml(self):
        toc = [
            {'index': [u'1000', u'1'], 
             'title': u'\xa7 1000.1 Authority, etc.'}, 
            {'index': [u'1000', u'2'], 
             'title': u'\xa7 1000.2 Definitions.'}, 
            {'index': [u'1000', u'A'], 
             'title': u'Appendix A to Part 1000'}
        ]
        expected_result = etree.fromstring('''
            <tableOfContents>
              <tocSecEntry target="1000-1">
                <sectionNum>1</sectionNum>
                <sectionSubject>&#167; 1000.1 Authority, etc.</sectionSubject>
              </tocSecEntry>
              <tocSecEntry target="1000-2">
                <sectionNum>2</sectionNum>
                <sectionSubject>&#167; 1000.2 Definitions.</sectionSubject>
              </tocSecEntry>
              <tocAppEntry target="1000-A">
                <appendixLetter>A</appendixLetter>
                <appendixSubject>Appendix A to Part 1000</appendixSubject>
              </tocAppEntry>
            </tableOfContents>
        ''', etree.XMLParser(remove_blank_text=True))
        result = XMLWriteContent.toc_to_xml(toc)
        self.assertEqual(etree.tostring(expected_result),
                etree.tostring(result))
    
    def test_is_interp_appendix(self):
        # XXX: This needs to be implemented
        self.assertTrue(False)

    def test_to_xml(self):
        # XXX: This test needs to be implemented
        self.assertTrue(False)

    def test_apply_layers(self):
        # XXX: This test needs to be implemented
        self.assertTrue(False)
        

class ClientTest(TestCase):

    def setUp(self):
        self.base = settings.API_BASE
        self.had_git_output = hasattr(settings, 'GIT_OUTPUT_DIR')
        self.old_git_output = getattr(settings, 'GIT_OUTPUT_DIR', '')
        settings.GIT_OUTPUT_DIR = ''

    def tearDown(self):
        settings.API_BASE = self.base
        if self.had_git_output:
            settings.GIT_OUTPUT_DIR = self.old_git_output
        else:
            del(settings.GIT_OUTPUT_DIR)

    def test_regulation(self):
        client = Client()
        reg_writer = client.regulation("lablab", "docdoc")
        self.assertEqual("regulation/lablab/docdoc", reg_writer.path)

    def test_layer(self):
        client = Client()
        reg_writer = client.layer("boblayer", "lablab", "docdoc")
        self.assertEqual("layer/boblayer/lablab/docdoc", reg_writer.path)

    def test_notice(self):
        client = Client()
        reg_writer = client.notice("docdoc")
        self.assertEqual("notice/docdoc", reg_writer.path)

    def test_diff(self):
        client = Client()
        reg_writer = client.diff("lablab", "oldold", "newnew")
        self.assertEqual("diff/lablab/oldold/newnew", reg_writer.path)

    def test_writer_class(self):
        settings.API_BASE = ''
        client = Client()
        self.assertEqual('FSWriteContent', client.writer_class.__name__)

        settings.GIT_OUTPUT_DIR = 'some path'
        client = Client()
        self.assertEqual('GitWriteContent', client.writer_class.__name__)
        settings.GIT_OUTPUT_DIR = ''

        settings.API_BASE = 'some url'
        client = Client()
        self.assertEqual('APIWriteContent', client.writer_class.__name__)

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

from mock import patch, mock_open
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
        writer = FSWriteContent("a/path/to/something", '1234-56789')
        writer.write({"testing": ["body", 1, 2]})

        wrote = json.loads(open(settings.OUTPUT_DIR
                                + '/a/path/to/something').read())
        self.assertEqual(wrote, {'testing': ['body', 1, 2]})

    def test_write_existing_dir(self):
        os.mkdir(settings.OUTPUT_DIR + 'existing')
        writer = FSWriteContent("existing/thing", '1234-56789')
        writer.write({"testing": ["body", 1, 2]})

        wrote = json.loads(open(settings.OUTPUT_DIR
                                + '/existing/thing').read())
        self.assertEqual(wrote, {'testing': ['body', 1, 2]})

    def test_write_overwrite(self):
        writer = FSWriteContent("replace/it", '1234-56789')
        writer.write({"testing": ["body", 1, 2]})

        writer = FSWriteContent("replace/it", '1234-56789')
        writer.write({"key": "value"})

        wrote = json.loads(open(settings.OUTPUT_DIR + '/replace/it').read())
        self.assertEqual(wrote, {'key': 'value'})

    def test_write_encoding(self):
        writer = FSWriteContent("replace/it", '1234-56789')
        writer.write({'text': 'Content'})

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
        writer = APIWriteContent("a/path", '1234-56789')
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

        writer = GitWriteContent("/regulation/1111/v1v1", '1234-56789')
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

        writer = GitWriteContent("/regulation/1111/v2v2", '1234-56789')
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

    @patch('regparser.api_writer.XMLWriteContent.write_notice')
    @patch('regparser.api_writer.XMLWriteContent.write_regulation')
    def test_write(self, write_regulation, write_notice):
        # layers = {'terms': {'referenced': {}},}
        writer = XMLWriteContent("a/path", '2015-12345', layers={}, notices={})

        # It should try to call write_regulation for this
        reg_tree = Node("Content", label=['1000'])
        writer.write(reg_tree)
        self.assertTrue(write_regulation.called)
        self.assertIn(reg_tree, write_regulation.call_args[0])

        # It should try to call write_regulation for this
        notice = {'document_number': '2015-12345'}
        writer.write(notice)
        self.assertTrue(write_notice.called)
        self.assertIn(notice, write_notice.call_args[0])

    def test_write_regulation(self):
        # XXX: This test needs to be implemented
        # self.assertTrue(False)
        pass

    @patch('regparser.api_writer.XMLWriteContent.build_analysis')
    @patch('regparser.api_writer.XMLWriteContent.fdsys')
    @patch('regparser.api_writer.XMLWriteContent.preamble')
    def test_write_notice(self, mock_preamble, mock_fdsys,
                          mock_build_analysis):
        changes = {'1234-2': {'op': 'modified'},
                   '1234-3': {'op': 'deleted'},
                   '1234-4': {'op': 'added'}}
        reg_tree = Node("I'm the root", label=['1234'], children=[
            Node("I'll get analysis", label=['1234', '1']),
            Node("I will be modified", label=['1234', '2']),
            Node("I will be deleted", label=['1234', '3']),
            Node("I will be added", label=['1234', '4']),
        ])

        # Ensure we have some analysis just to include
        layers = {'analyses': {'1234-1': [{}]}}
        mock_build_analysis.return_value = etree.fromstring("""
          <analysisSection target="1234-1" notice="2015-12345" date="">
            This is some analysis
          </analysisSection>
        """)

        # An FDSYS
        mock_fdsys.return_value = etree.fromstring("""
            <fdsys>
                This is an fdsys
            </fdsys>
        """)

        # A preamble
        mock_preamble.return_value = etree.fromstring("""
            <preamble>
                This is the preamble
            </preamble>
        """)

        writer = XMLWriteContent("a/path",
                                 '2015-12345',
                                 layers=layers,
                                 notices={})

        # Without reg_tree
        with self.assertRaises(RuntimeError):
            writer.write_notice({})

        # Write a notice file
        mock_file = mock_open()
        with patch.object(builtins, 'open', mock_file, create=True):
            writer.write_notice({}, changes=changes, reg_tree=reg_tree,
                                left_doc_number='2015-01234')

        # Get the resulting XML
        file_handle = mock_file()
        xml_string = file_handle.write.call_args[0][0]
        notice_xml = etree.fromstring(xml_string)

        # Introspect our changes
        changeset = notice_xml.find('.//{eregs}changeset')
        self.assertEqual('2015-01234',
                         changeset.get('leftDocumentNumber'))
        self.assertEqual('2015-12345',
                         changeset.get('rightDocumentNumber'))

        changes = notice_xml.findall('.//{eregs}change')
        self.assertEqual(len(changes), 4)
        self.assertEqual(
            2, len([c for c in changes if c.get('operation') == 'modified']))
        self.assertEqual(
            1, len([c for c in changes if c.get('operation') == 'deleted']))
        self.assertEqual(
            1, len([c for c in changes if c.get('operation') == 'added']))

        self.assertEqual(
            1, len(notice_xml.findall('./{eregs}analysis')))

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
        expected_definitions = {
            '1000-1-a': {'term': u'my defined term', 'offset': (0, 15)}
        }

        # extract_definitions is called in __init__ to create
        # layers['definitions']
        writer = XMLWriteContent("a/path", '2015-12345',
                                 layers=layers, notices={})
        definitions = writer.extract_definitions()
        self.assertEqual(expected_definitions, definitions)

    def test_apply_terms(self):
        text = "my defined term is my favorite of all the defined term" \
            "because it is mine"
        replacements = [{
            'ref': u'my defined term:1000-1-a',
            'offsets': [(0, 15)]
        }]
        expected_result = (
            [(0, 15)],
            ['<ref target="1000-1-a" reftype="term">my defined term</ref>']
        )
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
        expected_result = (
            [(22, 28)],
            ['<ref target="1000-1" reftype="internal">1000.1</ref>']
        )
        result = XMLWriteContent.apply_internal_citations(text, replacements)
        self.assertEqual(expected_result, result)

    def test_apply_external_citations(self):
        text = "Pub. L. 111-203, 124 Stat. 1376"
        replacements = [{
            'citation': [u'124', 'Stat.', u'1376'],
            'citation_type': 'STATUTES_AT_LARGE',
            'offsets': [[17, 31]]
        }]
        expected_result = (
            [[17, 31]],
            ['<ref target="STATUTES_AT_LARGE:124-Stat.-1376" '
             'reftype="external">124 Stat. 1376</ref>']
        )
        result = XMLWriteContent.apply_external_citations(text, replacements)
        self.assertEqual(expected_result, result)

    def test_apply_definitions(self):
        text = "my defined term is my favorite of all the defined term" \
            "because it is mine"
        replacement = {
            'term': u'my defined term',
            'offset': (0, 15)
        }
        expected_result = (
            [(0, 15)],
            ['<def term="my defined term">my defined term</def>']
        )
        result = XMLWriteContent.apply_definitions(text, replacement)
        self.assertEqual(expected_result, result)

    def test_apply_graphics(self):
        # XXX: This needs to be implemented
        # self.assertTrue(False)
        pass

    def test_apply_keyterms(self):
        text = "(a) A Keyterm. Some other text."
        replacements = [{'locations': [0], 'key_term': u'A Keyterm.'}]
        expected_result = ([(4, 14)], [''])
        result = XMLWriteContent.apply_keyterms(text, replacements)
        self.assertEqual(expected_result, result)

    def test_apply_formatting(self):
        # Test a table
        replacements = [{
            'text': '|Header row|\n|---|\n||',
            'locations': [0],
            'table_data': {'header': [[{'text': 'Header row',
                                        'rowspan': 1,
                                        'colspan': 1}]],
                           'rows': [['', '']]},
        }]
        expected_result = (
            [[0, 155]],
            ['<table><header><columnHeaderRow><column colspan="1" '
             'rowspan="1">Header row</column></columnHeaderRow>'
             '</header><row><cell></cell><cell></cell></row></table>']
        )
        result = XMLWriteContent.apply_formatting(replacements)
        self.assertEqual(expected_result, result)

        # Test dashes
        replacements = [{'text': u'Model form field_____',
                         'dash_data': {'text': u'Model form field'},
                         'locations': [0]}]
        expected_result = ([[0, 29]], [u'<dash>Model form field</dash>'])
        result = XMLWriteContent.apply_formatting(replacements)
        self.assertEqual(expected_result, result)

        # Test subscripts
        replacements = [{
            'locations': [0],
            'subscript_data': {
                "subscript": 'n',
                'variable': 'Val'
            },
            'text': 'Val_{n}'
        }]
        expected_result = (
            [[0, 48]],
            [u'<variable>Val<subscript>n</subscript></variable>']
        )
        result = XMLWriteContent.apply_formatting(replacements)
        self.assertEqual(expected_result, result)

        # Test fences
        # XXX: Actual fences need to be implemented
        replacements = [{
            'fence_data': {
                'lines': ['Note:', 'Note content.'],
                'type': 'note'
            },
            'locations': [0],
            'text': '```note\nNote:\nNote content.\n```'
        }]
        expected_result = (
            [[0, 76]],
            ['<callout type="note"><line>Note:</line>\n'
             '<line>Note content.</line></callout>']
        )
        result = XMLWriteContent.apply_formatting(replacements)
        self.assertEqual(expected_result, result)

    def test_add_analyses(self):
        """ Test that we can add analysis with sections within the
            primary section and footnotes. """
        layers = {
            'terms': {'referenced': {}},
            'analyses': {
                '1234-1': [{
                    'publication_date': u'2015-11-17',
                    'reference': (u'2015-12345', u'1234-1')
                }],
            }
        }
        notices = [{
            'document_number': '2015-12345',
            'section_by_section': [{
                'title': 'Section 1234.1',
                'labels': ['1234-1'],
                'paragraphs': [
                    'This paragraph is in the <EM>top-level</EM> section.',
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
        elm = etree.Element('regulation')
        writer = XMLWriteContent("a/path", '2015-12345',
                                 layers=layers, notices=notices)
        writer.add_analyses(elm)

        self.assertEqual(1, len(elm.xpath('./analysis')))
        self.assertEqual(
            1, len(elm.xpath('./analysis/analysisSection')))
        self.assertEqual(
            1, len(elm.xpath('./analysis/analysisSection/title')))
        self.assertEqual(
            'Section 1234.1',
            elm.xpath('./analysis/analysisSection/title')[0].text)

        self.assertEqual(
            1,
            len(elm.xpath('./analysis/analysisSection/analysisParagraph')))
        self.assertTrue(
            'top-level section' in
            elm.xpath('./analysis/analysisSection/analysisParagraph')[0].text)

        self.assertEqual(
            1,
            len(elm.xpath('./analysis/analysisSection/analysisSection')))
        self.assertEqual(
            1,
            len(elm.xpath('./analysis/analysisSection/analysisSection/title')))  # noqa
        self.assertEqual(
            '(a) Section of the Analysis',
            elm.xpath('./analysis/analysisSection/analysisSection/title')[0].text)  # noqa

        self.assertEqual(
            1,
            len(elm.xpath('./analysis/analysisSection/analysisSection/analysisParagraph')))  # noqa
        self.assertTrue(
            'I am a paragraph' in
            elm.xpath('./analysis/analysisSection/analysisSection/analysisParagraph')[0].text)  # noqa

        self.assertEqual(
            2,
            len(elm.xpath('./analysis/analysisSection/analysisSection/analysisParagraph/footnote')))  # noqa

        section = elm.find('./analysis/analysisSection')
        self.assertEqual('1234-1', section.get('target'))
        self.assertEqual('2015-12345', section.get('notice'))
        self.assertEqual('2015-11-17', section.get('date'))

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
        result = writer.fdsys('1000',
                              date='2015-01-01',
                              orig_date='2015-01-01')
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
        notices = [
            {'document_number': '2015-12345', 'fr_url': 'http://foo'},
            {'document_number': '2015-23456', 'fr_url': 'http://bar'},
        ]
        writer = XMLWriteContent("a/path", '2015-12345',
                                 layers=layers, notices=notices)
        expected_result = etree.fromstring('''
            <preamble>
              <agency>Bureau of Consumer Financial Protection</agency>
              <cfr>
                <title>12</title>
                <section>1000</section>
              </cfr>
              <documentNumber>2015-12345</documentNumber>
              <effectiveDate>2015-01-01</effectiveDate>
              <federalRegisterURL>http://foo</federalRegisterURL>
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
        # self.assertTrue(False)
        pass

    def test_to_xml(self):
        # XXX: This test needs to be implemented
        # self.assertTrue(False)
        pass

    def test_to_xml_title_text_node(self):
        """ Test that a node with title and text gets formatted
            correctly """
        node = Node(
            text=u'A Section',
            children=[
                Node(text=u'Paragraph text with title',
                     children=[
                         Node(text=u'Regular paragraph',
                              children=[],
                              label=[u'1111', u'1', 'a'],
                              title=u'',
                              node_type=u'regtext'),
                     ],
                     label=[u'1111', u'1', 'a'],
                     title=u'1. A Title',
                     node_type=u'regtext'),
            ],
            label=[u'1111', u'1'],
            title=u'A Title',
            node_type=u'regtext')
        layers = {
            'terms': {'referenced': {}},
            'graphics': {},
            'keyterms': {
                u'1111-1': [{'locations': [0],
                             'key_term': u'A Title.'}],
            },
            'paragraph-markers': {
                u'1111-1-a-Interp-1': [{
                    "text": "1.",
                    "locations": [0]
                }],
            },
        }
        notices = [{
            'document_number': '2015-12345',
        }]
        writer = XMLWriteContent("a/path", '2015-12345',
                                 layers=layers, notices=notices)
        writer.to_xml(node)

    def test_to_xml_interp(self):
        """ Test that interpretations get formatted correctly """
        interp_nodes = Node(
            text=u'',
            children=[
                Node(text=u'Interp for section',
                     children=[
                         Node(text=u'Interp targetting reg paragraph',
                              children=[
                                  Node(text=u'A Keyterm. Interp sp.',
                                       children=[],
                                       label=[u'1111',
                                              u'1',
                                              'a',
                                              u'Interp',
                                              u'1'],
                                       title=None,
                                       node_type=u'interp'),
                                  Node(text=u'Lone Keyterm. Or not.',
                                       children=[],
                                       label=[u'1111',
                                              u'1',
                                              'a',
                                              u'Interp',
                                              u'2'],
                                       title=None,
                                       node_type=u'interp'),
                              ],
                              label=[u'1111', u'1', 'a', u'Interp'],
                              title=u'1111.1 (a) Interp',
                              node_type=u'interp'),
                     ],
                     label=[u'1111', u'1', u'Interp'],
                     title=u'1111.1 Interp',
                     node_type=u'interp'),
            ],
            label=[u'1111', u'Interp'],
            title=u'Interpretations',
            node_type=u'interp')

        layers = {
            'terms': {
                "1111-1-a-Interp-2": [{
                    "offsets": [[0, 12]], "ref": "lone keyterm:1111-1-a"
                }],
                'referenced': {}},
            'graphics': {},
            'keyterms': {
                u'1111-1-a-Interp-1': [{'locations': [0],
                                        'key_term': u'A Keyterm.'}],
                u'1111-1-a-Interp-2': [{'locations': [0],
                                        'key_term': u'Lone Keyterm.'}],
            },
            'interpretations': {
                u'1111-1-a': [{'reference': u'1111-1-a-Interp'}],
            },
            'paragraph-markers': {
                u'1111-1-a-Interp-1': [{"text": "1.", "locations": [0]}],
                u'1111-1-a-Interp-2': [{"text": "2.", "locations": [0]}],
            },
        }
        notices = [{
            'document_number': '2015-12345',
        }]

        writer = XMLWriteContent("a/path", '2015-12345',
                                 layers=layers, notices=notices)

        elm = writer.to_xml(interp_nodes)

        interp_para = elm.find(
            './/interpParagraph[@label="1111-1-a-Interp"]')
        interp_sub_paras = interp_para.findall(
            'interpParagraph')

        # Check that paragraph targets are correct.
        self.assertEqual(interp_para.get('target'), '1111-1-a')
        self.assertEqual(interp_sub_paras[0].get('target'), None)

        # Check that title keyterm is correct
        self.assertNotEqual(interp_para.find('title'), None)
        self.assertEqual(interp_sub_paras[0].find('title').get('type'),
                         'keyterm')
        self.assertTrue('A Keyterm.' not in
                        interp_sub_paras[0].find('content').text)

        # For the second sub para there should be a <ref> in <title> and
        # nothing in content
        self.assertEqual(interp_sub_paras[1].find('title').get('type'),
                         'keyterm')
        self.assertTrue(interp_sub_paras[1].find('content').text is None)
        # self.assertTrue(len(interp_sub_paras[1].find('content')) is 0)

        # Check that paragraph markers are correct
        self.assertEqual(interp_para.get('marker'), None)
        self.assertEqual(interp_sub_paras[0].get('marker'), '1.')
        self.assertEqual(interp_sub_paras[1].get('marker'), '2.')

    def test_apply_layers(self):
        # XXX: This test needs to be implemented
        # self.assertTrue(False)
        pass


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
        reg_writer = client.notice("docdoc", '1234-56789')
        self.assertEqual("notice/docdoc/1234-56789", reg_writer.path)

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

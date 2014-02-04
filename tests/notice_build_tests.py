#vim: set encoding=utf-8
import os
import shutil
import tempfile
from unittest import TestCase

from lxml import etree
from mock import patch


from regparser.notice import build, changes
from regparser.notice.diff import DesignateAmendment, Amendment
from regparser.tree.struct import Node
import settings


class NoticeBuildTest(TestCase):
    def setUp(self):
        self.original_local_xml_paths = settings.LOCAL_XML_PATHS
        settings.LOCAL_XML_PATHS = []
        self.dir1 = tempfile.mkdtemp()
        self.dir2 = tempfile.mkdtemp()

    def tearDown(self):
        settings.LOCAL_XML_PATHS = self.original_local_xml_paths
        shutil.rmtree(self.dir1)
        shutil.rmtree(self.dir2)

    def test_build_notice(self):
        fr = {
            'abstract': 'sum sum sum',
            'action': 'actact',
            'agency_names': ['Agency 1', 'Agency 2'],
            'citation': 'citation citation',
            'comments_close_on': None,
            'dates': 'date info',
            'document_number': '7878-111',
            'effective_on': '1956-09-09',
            'end_page': 9999,
            'full_text_xml_url': None,
            'html_url': 'some url',
            'publication_date': '1955-12-10',
            'regulation_id_numbers': ['a231a-232q'],
            'start_page': 8888,
            'type': 'Rule',
            'volume': 66,
        }
        self.assertEqual(build.build_notice('5', '9292', fr), [{
            'abstract': 'sum sum sum',
            'action': 'actact',
            'agency_names': ['Agency 1', 'Agency 2'],
            'cfr_part': '9292',
            'cfr_title': '5',
            'document_number': '7878-111',
            'effective_on': '1956-09-09',
            'fr_citation': 'citation citation',
            'fr_url': 'some url',
            'fr_volume': 66,
            'initial_effective_on': '1956-09-09',
            'meta': {
                'dates': 'date info',
                'end_page': 9999,
                'start_page': 8888,
                'type': 'Rule'
            },
            'publication_date': '1955-12-10',
            'regulation_id_numbers': ['a231a-232q'],
        }])

    def test_process_xml(self):
        """Integration test for xml processing"""
        xml = """
        <ROOT>
            <SUPLINF>
                <FURINF>
                    <HD>CONTACT INFO:</HD>
                    <P>Extra contact info here</P>
                </FURINF>
                <ADD>
                    <P>Email: example@example.com</P>
                    <P>Extra instructions</P>
                </ADD>
                <HD SOURCE="HED">Supplementary Info</HD>
                <HD SOURCE="HD1">V. Section-by-Section Analysis</HD>
                <HD SOURCE="HD2">8(q) Words</HD>
                <P>Content</P>
                <HD SOURCE="HD1">Section that follows</HD>
                <P>Following Content</P>
            </SUPLINF>
        </ROOT>"""
        notice = {'cfr_part': '9292', 'meta': {'start_page': 100}}
        self.assertEqual(build.process_xml(notice, etree.fromstring(xml)), {
            'cfr_part': '9292',
            'footnotes': {},
            'meta': {'start_page': 100},
            'addresses': {
                'methods': [('Email', 'example@example.com')],
                'instructions': ['Extra instructions']
            },
            'contact': 'Extra contact info here',
            'section_by_section': [{
                'title': '8(q) Words',
                'paragraphs': ['Content'],
                'children': [],
                'footnote_refs': [],
                'page': 100,
                'label': '9292-8-q'
            }],
        })

    def test_process_xml_missing_fields(self):
        xml = """
        <ROOT>
            <SUPLINF>
                <HD SOURCE="HED">Supplementary Info</HD>
                <HD SOURCE="HD1">V. Section-by-Section Analysis</HD>
                <HD SOURCE="HD2">8(q) Words</HD>
                <P>Content</P>
                <HD SOURCE="HD1">Section that follows</HD>
                <P>Following Content</P>
            </SUPLINF>
        </ROOT>"""
        notice = {'cfr_part': '9292', 'meta': {'start_page': 210}}
        self.assertEqual(build.process_xml(notice, etree.fromstring(xml)), {
            'cfr_part': '9292',
            'footnotes': {},
            'meta': {'start_page': 210},
            'section_by_section': [{
                'title': '8(q) Words',
                'paragraphs': ['Content'],
                'children': [],
                'footnote_refs': [],
                'page': 210,
                'label': '9292-8-q'
            }],
        })

    def test_process_xml_fill_effective_date(self):
        xml = """
        <ROOT>
            <DATES>
                <P>Effective January 1, 2002</P>
            </DATES>
        </ROOT>"""
        xml = etree.fromstring(xml)

        notice = {'cfr_part': '902', 'meta': {'start_page': 10},
                  'effective_on': '2002-02-02'}
        notice = build.process_xml(notice, xml)
        self.assertEqual('2002-02-02', notice['effective_on'])

        notice = {'cfr_part': '902', 'meta': {'start_page': 10}}
        notice = build.process_xml(notice, xml)
        # Uses the date found in the XML
        self.assertEqual('2002-01-01', notice['effective_on'])

        notice = {'cfr_part': '902', 'meta': {'start_page': 10},
                  'effective_on': None}
        notice = build.process_xml(notice, xml)
        # Uses the date found in the XML
        self.assertEqual('2002-01-01', notice['effective_on'])

    def test_add_footnotes(self):
        xml = """
        <ROOT>
            <P>Some text</P>
            <FTNT>
                <P><SU>21</SU>Footnote text</P>
            </FTNT>
            <FTNT>
                <P><SU>43</SU>This has a<PRTPAGE P="2222" />break</P>
            </FTNT>
            <FTNT>
                <P><SU>98</SU>This one has<E T="03">emph</E>tags</P>
            </FTNT>
        </ROOT>"""
        notice = {}
        build.add_footnotes(notice, etree.fromstring(xml))
        self.assertEqual(notice, {'footnotes': {
            '21': 'Footnote text',
            '43': 'This has a break',
            '98': 'This one has <em data-original="E-03">emph</em> tags'
        }})

    def test_process_designate_subpart(self):
        p_list = ['200-?-1-a', '200-?-1-b']
        destination = '205-Subpart:A'
        amended_label = DesignateAmendment('DESIGNATE', p_list, destination)

        subpart_changes = build.process_designate_subpart(amended_label)

        self.assertEqual(['200-1-a', '200-1-b'], subpart_changes.keys())

        for p, change in subpart_changes.items():
            self.assertEqual(change['destination'], ['205', 'Subpart', 'A'])
            self.assertEqual(change['action'], 'DESIGNATE')

    def test_process_amendments(self):
        xml = u"""
        <REGTEXT PART="105" TITLE="12">
        <SUBPART>
        <HD SOURCE="HED">Subpart A—General</HD>
        </SUBPART>
        <AMDPAR>
        2. Designate §§ 105.1 through 105.3 as subpart A under the heading.
        </AMDPAR>
        </REGTEXT>"""

        notice_xml = etree.fromstring(xml)
        notice = {}
        build.process_amendments(notice, notice_xml)

        section_list = ['105-2', '105-3', '105-1']
        self.assertEqual(notice['changes'].keys(), section_list)

        for l, c in notice['changes'].items():
            change = c[0]
            self.assertEqual(change['destination'], ['105', 'Subpart', 'A'])
            self.assertEqual(change['action'], 'DESIGNATE')

    def test_process_amendments_section(self):
        xml = u"""
            <REGTEXT PART="105" TITLE="12">
            <AMDPAR>
            3. In § 105.1, revise paragraph (b) to read as follows:
            </AMDPAR>
            <SECTION>
                <SECTNO>§ 105.1</SECTNO>
                <SUBJECT>Purpose.</SUBJECT>
                <STARS/>
                <P>(b) This part carries out.</P>
            </SECTION>
            </REGTEXT>
        """

        notice_xml = etree.fromstring(xml)
        notice = {'cfr_part': '105'}
        build.process_amendments(notice, notice_xml)

        self.assertEqual(notice['changes'].keys(), ['105-1-b'])

        changes = notice['changes']['105-1-b'][0]
        self.assertEqual(changes['action'], 'PUT')
        self.assertTrue(changes['node']['text'].startswith(
            u'(b) This part carries out.'))

    def test_process_amendments_multiple_in_same_parent(self):
        xml = u"""
            <REGTEXT PART="105" TITLE="12">
                <AMDPAR>
                    1. In § 105.1, revise paragraph (b) to read as follows:
                </AMDPAR>
                <AMDPAR>2. Also, revise paragraph (c):</AMDPAR>
                <SECTION>
                    <SECTNO>§ 105.1</SECTNO>
                    <SUBJECT>Purpose.</SUBJECT>
                    <STARS/>
                    <P>(b) This part carries out.</P>
                    <P>(c) More stuff</P>
                </SECTION>
            </REGTEXT>"""

        notice_xml = etree.fromstring(xml)
        notice = {'cfr_part': '105'}
        build.process_amendments(notice, notice_xml)

        self.assertEqual(notice['changes'].keys(), ['105-1-b', '105-1-c'])

        changes = notice['changes']['105-1-b'][0]
        self.assertEqual(changes['action'], 'PUT')
        self.assertEqual(changes['node']['text'].strip(),
                         u'(b) This part carries out.')
        changes = notice['changes']['105-1-c'][0]
        self.assertEqual(changes['action'], 'PUT')
        self.assertTrue(changes['node']['text'].strip(),
                        u'(c) More stuff')

    def new_subpart_xml(self):
        xml = u"""
            <RULE>
            <REGTEXT PART="105" TITLE="12">
            <AMDPAR>
            3. In § 105.1, revise paragraph (b) to read as follows:
            </AMDPAR>
            <SECTION>
                <SECTNO>§ 105.1</SECTNO>
                <SUBJECT>Purpose.</SUBJECT>
                <STARS/>
                <P>(b) This part carries out.</P>
            </SECTION>
            </REGTEXT>
           <REGTEXT PART="105" TITLE="12">
            <AMDPAR>
                6. Add subpart B to read as follows:
            </AMDPAR>
            <CONTENTS>
                <SUBPART>
                    <SECHD>Sec.</SECHD>
                    <SECTNO>105.30</SECTNO>
                    <SUBJECT>First In New Subpart.</SUBJECT>
                </SUBPART>
            </CONTENTS>
            <SUBPART>
                <HD SOURCE="HED">Subpart B—Requirements</HD>
                <SECTION>
                    <SECTNO>105.30</SECTNO>
                    <SUBJECT>First In New Subpart</SUBJECT>
                    <P>For purposes of this subpart, the follow apply:</P>
                    <P>(a) "Agent" means agent.</P>
                </SECTION>
            </SUBPART>
           </REGTEXT>
           </RULE>"""

        return xml

    def test_process_new_subpart(self):
        xml = self.new_subpart_xml()
        notice_xml = etree.fromstring(xml)
        par = notice_xml.xpath('//AMDPAR')[1]

        amended_label = ('POST', '105-Subpart:B')
        notice = {'cfr_part': '105'}
        changes = build.process_new_subpart(notice, amended_label, par)

        new_nodes_added = ['105-Subpart-B', '105-30', '105-30-a']
        self.assertEqual(new_nodes_added, changes.keys())

        for l, n in changes.items():
            self.assertEqual(n['action'], 'POST')

        self.assertEqual(
            changes['105-Subpart-B']['node']['node_type'], 'subpart')

    def test_process_amendments_subpart(self):
        xml = self.new_subpart_xml()

        notice_xml = etree.fromstring(xml)
        notice = {'cfr_part': '105'}
        build.process_amendments(notice, notice_xml)

        self.assertTrue('105-Subpart-B' in notice['changes'].keys())
        self.assertTrue('105-30-a' in notice['changes'].keys())
        self.assertTrue('105-30' in notice['changes'].keys())

    def test_process_amendments_other_reg(self):
        """Some notices apply to multiple regs. For now, just ignore the
        sections not associated with the reg we're focused on"""
        xml = u"""
            <REGTEXT PART="106" TITLE="12">
            <AMDPAR>
            3. In § 106.1, revise paragraph (a) to read as follows:
            </AMDPAR>
            <SECTION>
                <SECTNO>§ 106.1</SECTNO>
                <SUBJECT>Purpose.</SUBJECT>
                <P>(a) Content</P>
            </SECTION>
            </REGTEXT>
        """

        notice_xml = etree.fromstring(xml)
        notice = {'cfr_part': '105'}
        build.process_amendments(notice, notice_xml)

        self.assertEqual({}, notice['changes'])

    def test_introductory_text(self):
        """ Sometimes notices change just the introductory text of a paragraph
        (instead of changing the entire paragraph tree).  """

        xml = u"""
        <REGTEXT PART="106" TITLE="12">
        <AMDPAR>
            3. In § 106.2, revise the introductory text to read as follows:
        </AMDPAR>
        <SECTION>
            <SECTNO>§ 106.2</SECTNO>
            <SUBJECT> Definitions </SUBJECT>
            <P> Except as otherwise provided, the following apply. </P>
        </SECTION>
        </REGTEXT>
        """

        notice_xml = etree.fromstring(xml)
        notice = {'cfr_part': '106'}
        build.process_amendments(notice, notice_xml)

        self.assertEqual('[text]', notice['changes']['106-2'][0]['field'])

    def test_multiple_changes(self):
        """ A notice can have two modifications to a paragraph. """

        xml = u"""
        <ROOT>
        <REGTEXT PART="106" TITLE="12">
        <AMDPAR>
            2. Designate §§ 106.1 through 106.3 as subpart A under the heading.
        </AMDPAR>
        </REGTEXT>
        <REGTEXT PART="106" TITLE="12">
        <AMDPAR>
            3. In § 106.2, revise the introductory text to read as follows:
        </AMDPAR>
        <SECTION>
            <SECTNO>§ 106.2</SECTNO>
            <SUBJECT> Definitions </SUBJECT>
            <P> Except as otherwise provided, the following apply. </P>
        </SECTION>
        </REGTEXT>
        </ROOT>
        """

        notice_xml = etree.fromstring(xml)
        notice = {'cfr_part': '106'}
        build.process_amendments(notice, notice_xml)

        self.assertEqual(2, len(notice['changes']['106-2']))

    def test_create_changes_reserve(self):
        labels_amended = [Amendment('RESERVE', '200-2-a')]

        n2a = Node('[Reserved]', label=['200', '2', 'a'])
        n2 = Node('n2', label=['200', '2'], children=[n2a])
        root = Node('root', label=['200'], children=[n2])

        notice_changes = changes.NoticeChanges()
        build.create_changes(labels_amended, root, notice_changes)

        reserve = notice_changes.changes['200-2-a'][0]
        self.assertEqual(reserve['action'], 'RESERVE')
        self.assertEqual(reserve['node']['text'], u'[Reserved]')

    def test_local_version_list(self):
        url = 'http://example.com/some/url'

        settings.LOCAL_XML_PATHS = [self.dir1, self.dir2]
        os.mkdir(self.dir2 + '/some')
        f = open(self.dir2 + '/some/url', 'w')
        f.write('aaaaa')
        f.close()

        local_file = self.dir2 + '/some/url'
        self.assertEqual([local_file], build._check_local_version_list(url))

        os.mkdir(self.dir1 + '/some')
        f = open(self.dir1 + '/some/url', 'w')
        f.write('bbbbb')
        f.close()
        local_file_2 = self.dir1 + '/some/url'
        self.assertEqual([local_file_2], build._check_local_version_list(url))

    def test_local_version_list_split(self):
        settings.LOCAL_XML_PATHS = [self.dir1, self.dir2]

        os.mkdir(self.dir2 + '/xml/')
        f = open(self.dir2 + '/xml/503-1.xml', 'w')
        f.write('first_file')
        f.close()

        f = open(self.dir2 + '/xml/503-2.xml', 'w')
        f.write('second_file')

        url = 'http://example.com/xml/503.xml'

        first = self.dir2 + '/xml/503-1.xml'
        second = self.dir2 + '/xml/503-2.xml'

        local_versions = build._check_local_version_list(url)
        local_versions.sort()
        self.assertEqual([first, second], local_versions)

    def test_split_doc_num(self):
        doc_num = '2013-2222'
        effective_date = '2014-10-11'
        self.assertEqual(
            '2013-2222_20141011',
            build.split_doc_num(doc_num, effective_date))

    @patch('regparser.notice.build.interpretations')
    def test_parse_interp_changes(self, interpretations):
        xml_str1 = """
            <REGTEXT>
                <EXTRACT>
                    <P>Something</P>
                    <STARS />
                    <HD>Supplement I</HD>
                    <HD>A</HD>
                    <T1>a</T1>
                    <P>b</P>
                </EXTRACT>
            </REGTEXT>"""

        xml_str2 = """
            <REGTEXT>
                <P>Something</P>
                <STARS />
                <SUBSECT><HD>Supplement I</HD></SUBSECT>
                <HD>A</HD>
                <T1>a</T1>
                <P>b</P>
            </REGTEXT>"""
        xml_str3 = """
            <REGTEXT>
                <AMDPAR>1. In Supplement I to part 111, under...</AMDPAR>
                <P>Something</P>
                <STARS />
                <HD>SUPPLEMENT I</HD>
                <HD>A</HD>
                <T1>a</T1>
                <P>b</P>
            </REGTEXT>"""
        xml_str4 = """
            <REGTEXT>
                <AMDPAR>1. In Supplement I to part 111, under...</AMDPAR>
                <P>Something</P>
                <STARS />
                <APPENDIX>
                    <HD>SUPPLEMENT I</HD>
                </APPENDIX>
                <HD>A</HD>
                <T1>a</T1>
                <P>b</P>
                <PRTPAGE />
            </REGTEXT>"""

        for xml_str in (xml_str1, xml_str2, xml_str3, xml_str4):
            build.parse_interp_changes('111', etree.fromstring(xml_str))
            root, nodes = interpretations.parse_from_xml.call_args[0]
            self.assertEqual(root.label, ['111', 'Interp'])
            self.assertEqual(['HD', 'T1', 'P'], [n.tag for n in nodes])

    def test_set_document_numbers(self):
        notice = {'document_number': '111', 'effective_on': '2013-10-08'}
        notices = build.set_document_numbers([notice])
        self.assertEqual(notices[0]['document_number'], '111')

        second_notice = {'document_number': '222',
                         'effective_on': '2013-10-10'}

        notices = build.set_document_numbers([notice, second_notice])

        self.assertEqual(notices[0]['document_number'], '111_20131008')
        self.assertEqual(notices[1]['document_number'], '222_20131010')

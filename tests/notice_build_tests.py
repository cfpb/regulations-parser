# vim: set encoding=utf-8
import os
import shutil
import tempfile
from unittest import TestCase

from lxml import etree

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
            'cfr_references': [{'title': 12, 'part': 9191},
                               {'title': 12, 'part': 9292}],
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
            'cfr_parts': ['9191', '9292'],
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

    def test_build_notice_override_fr(self):
        """ Test that the FR_NOTICE_OVERRIDES setting can override the
        'dates' value from build_notice """
        fr = {
            'abstract': 'sum sum sum',
            'action': 'actact',
            'agency_names': ['Agency 1', 'Agency 2'],
            'cfr_references': [{'title': 12, 'part': 9191},
                               {'title': 12, 'part': 9292}],
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

        # Set our override value
        build.settings.FR_NOTICE_OVERRIDES['7878-111'] = {
            'dates': 'new date info',
        }

        self.assertEqual(build.build_notice('5', '9292', fr), [{
            'abstract': 'sum sum sum',
            'action': 'actact',
            'agency_names': ['Agency 1', 'Agency 2'],
            'cfr_parts': ['9191', '9292'],
            'cfr_part': '9292',
            'cfr_title': '5',
            'document_number': '7878-111',
            'effective_on': '1956-09-09',
            'fr_citation': 'citation citation',
            'fr_url': 'some url',
            'fr_volume': 66,
            'initial_effective_on': '1956-09-09',
            'meta': {
                'dates': 'new date info',
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
        notice = {'cfr_parts': ['9292'], 'cfr_part': '9292',
                  'meta': {'start_page': 100},
                  'document_number': '1999-12345'}
        self.assertEqual(build.process_xml(notice, etree.fromstring(xml)), {
            'cfr_parts': ['9292'],
            'cfr_part': '9292',
            'footnotes': {},
            'meta': {'start_page': 100},
            'document_number': '1999-12345',
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
                'labels': ['9292-8-q']
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
        notice = {'cfr_parts': ['9292'], 'cfr_part': '9292',
                  'meta': {'start_page': 210},
                  'document_number': '1999-12345'}
        self.assertEqual(build.process_xml(notice, etree.fromstring(xml)), {
            'cfr_parts': ['9292'],
            'cfr_part': '9292',
            'footnotes': {},
            'meta': {'start_page': 210},
            'document_number': '1999-12345',
            'section_by_section': [{
                'title': '8(q) Words',
                'paragraphs': ['Content'],
                'children': [],
                'footnote_refs': [],
                'page': 210,
                'labels': ['9292-8-q']
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

        notice = {'cfr_parts': ['902'], 'cfr_part': '902',
                  'meta': {'start_page': 10},
                  'document_number': '1999-12345',
                  'effective_on': '2002-02-02'}
        notice = build.process_xml(notice, xml)
        self.assertEqual('2002-02-02', notice['effective_on'])

        notice = {'cfr_parts': ['902'], 'cfr_part': '902',
                  'meta': {'start_page': 10},
                  'document_number': '1999-12345'}
        notice = build.process_xml(notice, xml)
        # Uses the date found in the XML
        self.assertEqual('2002-01-01', notice['effective_on'])

        notice = {'cfr_parts': ['902'], 'cfr_part': '902',
                  'meta': {'start_page': 10},
                  'document_number': '1999-12345', 'effective_on': None}
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
        notice = {'cfr_parts': ['105'], 'cfr_part': '105'}
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
        notice = {'cfr_parts': ['105'], 'cfr_part': '105'}
        build.process_amendments(notice, notice_xml)

        self.assertEqual(notice['changes'].keys(), ['105-1-b'])

        changes = notice['changes']['105-1-b'][0]
        self.assertEqual(changes['action'], 'PUT')
        self.assertTrue(changes['node'].text.startswith(
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
        notice = {'cfr_parts': ['105'], 'cfr_part': '105'}
        build.process_amendments(notice, notice_xml)

        self.assertEqual(notice['changes'].keys(), ['105-1-b', '105-1-c'])

        changes = notice['changes']['105-1-b'][0]
        self.assertEqual(changes['action'], 'PUT')
        self.assertEqual(changes['node'].text.strip(),
                         u'(b) This part carries out.')
        changes = notice['changes']['105-1-c'][0]
        self.assertEqual(changes['action'], 'PUT')
        self.assertTrue(changes['node'].text.strip(),
                        u'(c) More stuff')

    def test_process_amendments_restart_new_section(self):
        xml = u"""
        <ROOT>
            <REGTEXT PART="104" TITLE="12">
                <AMDPAR>
                    1. In Supplement I to Part 104, comment 22(a) is added
                </AMDPAR>
                <P>Content</P>
            </REGTEXT>
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
        </ROOT>"""

        notice_xml = etree.fromstring(xml)
        notice = {'cfr_parts': ['105'], 'cfr_part': '105'}
        build.process_amendments(notice, notice_xml)

        self.assertEqual(2, len(notice['amendments']))
        c22a, b = notice['amendments']
        self.assertEqual(c22a.action, 'POST')
        self.assertEqual(b.action, 'PUT')
        self.assertEqual(c22a.label, ['104', '22', 'a', 'Interp'])
        self.assertEqual(b.label, ['105', '1', 'b'])

    def test_process_amendments_no_nodes(self):
        xml = u"""
        <ROOT>
            <REGTEXT PART="104" TITLE="12">
                <AMDPAR>
                    1. In § 104.13, paragraph (b) is removed
                </AMDPAR>
            </REGTEXT>
        </ROOT>"""

        notice_xml = etree.fromstring(xml)
        notice = {'cfr_parts': ['104'], 'cfr_part': '104'}
        build.process_amendments(notice, notice_xml)

        self.assertEqual(1, len(notice['amendments']))
        delete = notice['amendments'][0]
        self.assertEqual(delete.action, 'DELETE')
        self.assertEqual(delete.label, ['104', '13', 'b'])

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

        amended_label = Amendment('POST', '105-Subpart:B')
        notice = {'cfr_parts': ['105'], 'cfr_part': '105'}
        subpart_changes = build.process_new_subpart(notice, amended_label, par)

        new_nodes_added = ['105-Subpart-B', '105-30', '105-30-a']
        self.assertEqual(new_nodes_added, subpart_changes.keys())

        for l, n in subpart_changes.items():
            self.assertEqual(n['action'], 'POST')

        self.assertEqual(
            subpart_changes['105-Subpart-B']['node'].node_type, 'subpart')

    def test_process_amendments_subpart(self):
        xml = self.new_subpart_xml()

        notice_xml = etree.fromstring(xml)
        notice = {'cfr_parts': ['105'], 'cfr_part': '105'}
        build.process_amendments(notice, notice_xml)

        self.assertTrue('105-Subpart-B' in notice['changes'].keys())
        self.assertTrue('105-30-a' in notice['changes'].keys())
        self.assertTrue('105-30' in notice['changes'].keys())

    def test_process_amendments_mix_regs(self):
        """Some notices apply to multiple regs. For now, just ignore the
        sections not associated with the reg we're focused on"""
        xml = u"""
            <ROOT>
            <REGTEXT PART="105" TITLE="12">
                <AMDPAR>
                3. In § 105.1, revise paragraph (a) to read as follows:
                </AMDPAR>
                <SECTION>
                    <SECTNO>§ 105.1</SECTNO>
                    <SUBJECT>105Purpose.</SUBJECT>
                    <P>(a) 105Content</P>
                </SECTION>
            </REGTEXT>
            <REGTEXT PART="106" TITLE="12">
                <AMDPAR>
                3. In § 106.3, revise paragraph (b) to read as follows:
                </AMDPAR>
                <SECTION>
                    <SECTNO>§ 106.3</SECTNO>
                    <SUBJECT>106Purpose.</SUBJECT>
                    <P>(b) Content</P>
                </SECTION>
            </REGTEXT>
            </ROOT>
        """

        notice_xml = etree.fromstring(xml)
        notice = {'cfr_parts': ['105', '106'], 'cfr_part': '105'}
        build.process_amendments(notice, notice_xml)

        self.assertEqual(1, len(notice['changes']))
        self.assertTrue('105-1-a' in notice['changes'])
        self.assertTrue('106-3-b' not in notice['changes'])

    def test_process_amendments_context(self):
        """Context should carry over between REGTEXTs"""
        xml = u"""
            <ROOT>
            <REGTEXT TITLE="12">
                <AMDPAR>
                3. In § 106.1, revise paragraph (a) to read as follows:
                </AMDPAR>
            </REGTEXT>
            <REGTEXT TITLE="12">
                <AMDPAR>
                3. Add appendix C
                </AMDPAR>
            </REGTEXT>
            </ROOT>
        """

        notice_xml = etree.fromstring(xml)
        notice = {'cfr_parts': ['106', '105'], 'cfr_part': '106'}
        build.process_amendments(notice, notice_xml)

        self.assertEqual(2, len(notice['amendments']))
        amd1, amd2 = notice['amendments']
        self.assertEqual(['106', '1', 'a'], amd1.label)
        self.assertEqual(['106', 'C'], amd2.label)

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
        notice = {'cfr_parts': ['106'], 'cfr_part': '106'}
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
        notice = {'cfr_parts': ['106'], 'cfr_part': '106'}
        build.process_amendments(notice, notice_xml)

        self.assertEqual(2, len(notice['changes']['106-2']))

    def test_create_xmlless_changes(self):
        labels_amended = [Amendment('DELETE', '200-2-a'),
                          Amendment('MOVE', '200-2-b', '200-2-c')]
        notice_changes = changes.NoticeChanges()
        build.create_xmlless_changes(labels_amended, notice_changes)

        delete = notice_changes.changes['200-2-a'][0]
        move = notice_changes.changes['200-2-b'][0]
        self.assertEqual({'action': 'DELETE'}, delete)
        self.assertEqual({'action': 'MOVE', 'destination': ['200', '2', 'c']},
                         move)

    def test_create_xml_changes_reserve(self):
        labels_amended = [Amendment('RESERVE', '200-2-a')]

        n2a = Node('[Reserved]', label=['200', '2', 'a'])
        n2 = Node('n2', label=['200', '2'], children=[n2a])
        root = Node('root', label=['200'], children=[n2])

        notice_changes = changes.NoticeChanges()
        build.create_xml_changes(labels_amended, root, notice_changes)

        reserve = notice_changes.changes['200-2-a'][0]
        self.assertEqual(reserve['action'], 'RESERVE')
        self.assertEqual(reserve['node'].text, u'[Reserved]')

    def test_create_xml_changes_stars(self):
        labels_amended = [Amendment('PUT', '200-2-a')]
        n2a1 = Node('(1) Content', label=['200', '2', 'a', '1'])
        n2a2 = Node('(2) Content', label=['200', '2', 'a', '2'])
        n2a = Node('(a) * * *', label=['200', '2', 'a'], children=[n2a1, n2a2])
        n2 = Node('n2', label=['200', '2'], children=[n2a])
        root = Node('root', label=['200'], children=[n2])

        notice_changes = changes.NoticeChanges()
        build.create_xml_changes(labels_amended, root, notice_changes)

        for label in ('200-2-a-1', '200-2-a-2'):
            self.assertTrue(label in notice_changes.changes)
            self.assertEqual(1, len(notice_changes.changes[label]))
            change = notice_changes.changes[label][0]
            self.assertEqual('PUT', change['action'])
            self.assertFalse('field' in change)

        self.assertTrue('200-2-a' in notice_changes.changes)
        self.assertEqual(1, len(notice_changes.changes['200-2-a']))
        change = notice_changes.changes['200-2-a'][0]
        self.assertEqual('KEEP', change['action'])
        self.assertFalse('field' in change)

    def test_create_xml_changes_stars_hole(self):
        labels_amended = [Amendment('PUT', '200-2-a')]
        n2a1 = Node('(1) * * *', label=['200', '2', 'a', '1'])
        n2a2 = Node('(2) a2a2a2', label=['200', '2', 'a', '2'])
        n2a = Node('(a) aaa', label=['200', '2', 'a'], children=[n2a1, n2a2])
        n2 = Node('n2', label=['200', '2'], children=[n2a])
        root = Node('root', label=['200'], children=[n2])

        notice_changes = changes.NoticeChanges()
        build.create_xml_changes(labels_amended, root, notice_changes)

        for label in ('200-2-a', '200-2-a-2'):
            self.assertTrue(label in notice_changes.changes)
            self.assertEqual(1, len(notice_changes.changes[label]))
            change = notice_changes.changes[label][0]
            self.assertEqual('PUT', change['action'])
            self.assertFalse('field' in change)

        self.assertTrue('200-2-a-1' in notice_changes.changes)
        self.assertEqual(1, len(notice_changes.changes['200-2-a-1']))
        change = notice_changes.changes['200-2-a-1'][0]
        self.assertEqual('KEEP', change['action'])
        self.assertFalse('field' in change)

    def test_create_xml_changes_child_stars(self):
        labels_amended = [Amendment('PUT', '200-2-a')]
        xml = etree.fromstring("<ROOT><P>(a) Content</P><STARS /></ROOT>")
        n2a = Node('(a) Content', label=['200', '2', 'a'],
                   source_xml=xml.xpath('//P')[0])
        n2b = Node('(b) Content', label=['200', '2', 'b'])
        n2 = Node('n2', label=['200', '2'], children=[n2a, n2b])
        root = Node('root', label=['200'], children=[n2])

        notice_changes = changes.NoticeChanges()
        build.create_xml_changes(labels_amended, root, notice_changes)

        self.assertTrue('200-2-a' in notice_changes.changes)
        self.assertTrue(1, len(notice_changes.changes['200-2-a']))
        change = notice_changes.changes['200-2-a'][0]
        self.assertEqual('PUT', change['action'])
        self.assertFalse('field' in change)

        n2a.text = n2a.text + ":"
        n2a.source_xml.text = n2a.source_xml.text + ":"

        notice_changes = changes.NoticeChanges()
        build.create_xml_changes(labels_amended, root, notice_changes)

        self.assertTrue('200-2-a' in notice_changes.changes)
        self.assertTrue(1, len(notice_changes.changes['200-2-a']))
        change = notice_changes.changes['200-2-a'][0]
        self.assertEqual('PUT', change['action'])
        self.assertEqual('[text]', change.get('field'))

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

    def test_set_document_numbers(self):
        notice = {'document_number': '111', 'effective_on': '2013-10-08'}
        notices = build.set_document_numbers([notice])
        self.assertEqual(notices[0]['document_number'], '111')

        second_notice = {'document_number': '222',
                         'effective_on': '2013-10-10'}

        notices = build.set_document_numbers([notice, second_notice])

        self.assertEqual(notices[0]['document_number'], '111_20131008')
        self.assertEqual(notices[1]['document_number'], '222_20131010')

    def test_preprocess_notice_xml_improper_location(self):
        notice_xml = etree.fromstring(u"""
            <PART>
                <REGTEXT>
                    <AMDPAR>1. In § 105.1, revise paragraph (b):</AMDPAR>
                    <SECTION>
                        <STARS />
                        <P>(b) Content</P>
                    </SECTION>
                    <AMDPAR>
                        3. In § 105.2, revise paragraph (a) to read as follows:
                    </AMDPAR>
                </REGTEXT>
                <REGTEXT>
                    <SECTION>
                        <P>(a) Content</P>
                    </SECTION>
                </REGTEXT>
            </PART>""")
        notice_xml = build.preprocess_notice_xml(notice_xml)
        amd1b, amd2a = notice_xml.xpath("//AMDPAR")
        self.assertEqual(amd1b.getparent().xpath(".//P")[0].text.strip(),
                         "(b) Content")
        self.assertEqual(amd2a.getparent().xpath(".//P")[0].text.strip(),
                         "(a) Content")

        notice_xml = etree.fromstring(u"""
            <PART>
                <REGTEXT PART="105">
                    <AMDPAR>1. In § 105.1, revise paragraph (b):</AMDPAR>
                    <SECTION>
                        <STARS />
                        <P>(b) Content</P>
                    </SECTION>
                    <AMDPAR>
                        3. In § 105.2, revise paragraph (a) to read as follows:
                    </AMDPAR>
                </REGTEXT>
                <REGTEXT PART="107">
                    <SECTION>
                        <P>(a) Content</P>
                    </SECTION>
                </REGTEXT>
            </PART>""")
        notice_xml = build.preprocess_notice_xml(notice_xml)
        amd1b, amd2a = notice_xml.xpath("//AMDPAR")
        self.assertEqual(amd1b.getparent().xpath(".//P")[0].text.strip(),
                         "(b) Content")
        self.assertEqual(amd2a.getparent().xpath(".//P")[0].text.strip(),
                         "(b) Content")

    def test_preprocess_notice_xml_interp_amds_are_ps(self):
        notice_xml = etree.fromstring(u"""
            <PART>
                <REGTEXT>
                    <AMDPAR>1. In § 105.1, revise paragraph (b):</AMDPAR>
                    <SECTION>
                        <STARS />
                        <P>(b) Content</P>
                    </SECTION>
                    <P>2. In Supplement I to Part 105,</P>
                    <P>A. Under Section 105.1, 1(b), paragraph 2 is revised</P>
                    <P>The revisions are as follows</P>
                    <HD SOURCE="HD1">Supplement I to Part 105</HD>
                    <STARS />
                    <P><E T="03">1(b) Heading</E></P>
                    <STARS />
                    <P>2. New Content</P>
                </REGTEXT>
            </PART>""")
        notice_xml = build.preprocess_notice_xml(notice_xml)
        amd1, amd2, amd2A, amd_other = notice_xml.xpath("//AMDPAR")
        self.assertEqual(amd2A.text.strip(), "A. Under Section 105.1, 1(b), "
                                             + "paragraph 2 is revised")

    def test_preprocess_notice_xml_interp_amds_are_ps2(self):
        notice_xml = etree.fromstring(u"""
            <PART>
                <REGTEXT>
                    <AMDPAR>1. In Supplement I to Part 105,</AMDPAR>
                    <P>A. Under Section 105.1, 1(b), paragraph 2 is revised</P>
                    <P>The revisions are as follows</P>
                    <HD SOURCE="HD1">Supplement I to Part 105</HD>
                    <STARS />
                    <P><E T="03">1(b) Heading</E></P>
                    <STARS />
                    <P>2. New Content</P>
                </REGTEXT>
            </PART>""")
        notice_xml = build.preprocess_notice_xml(notice_xml)
        amd1, amd1A, amd_other = notice_xml.xpath("//AMDPAR")
        self.assertEqual(amd1A.text.strip(), "A. Under Section 105.1, 1(b), "
                                             + "paragraph 2 is revised")

    def test_preprocess_emph_tags(self):
        notice_xml = etree.fromstring(u"""
            <PART>
                <P>(<E T="03">a</E>) Content</P>
                <P>(<E T="03">a)</E> Content</P>
                <P><E T="03">(a</E>) Content</P>
                <P><E T="03">(a)</E> Content</P>
            </PART>""")
        notice_xml = build.preprocess_notice_xml(notice_xml)
        pars = notice_xml.xpath("//P")
        self.assertEqual(4, len(pars))
        for par in pars:
            self.assertEqual(par.text, "(")
            self.assertEqual(1, len(par.getchildren()))
            em = par.getchildren()[0]
            self.assertEqual("E", em.tag)
            self.assertEqual("a", em.text)
            self.assertEqual(em.tail, ") Content")
            self.assertEqual(0, len(em.getchildren()))

        notice_xml = etree.fromstring(u"""
            <PART>
                <P><E T="03">Paragraph 22(a)(5)</E> Content</P>
            </PART>""")
        notice_xml = build.preprocess_notice_xml(notice_xml)
        pars = notice_xml.xpath("//P")
        self.assertEqual(1, len(pars))
        em = pars[0].getchildren()[0]
        self.assertEqual(em.text, "Paragraph 22(a)(5)")
        self.assertEqual(em.tail, " Content")

    def test_fetch_cfr_parts(self):
        notice_xml = etree.fromstring(u"""
            <RULE>
                <PREAMB>
                    <CFR>12 CFR Parts 1002, 1024, and 1026</CFR>
                </PREAMB>
            </RULE>
          """)

        result = build.fetch_cfr_parts(notice_xml)
        self.assertEqual(result, ['1002', '1024', '1026'])

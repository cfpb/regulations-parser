#vim: set encoding=utf-8
from lxml import etree
from regparser.notice import build
from unittest import TestCase


class NoticeBuildTest(TestCase):

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
        self.assertEqual(build.build_notice('5', '9292', fr), {
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
        })

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
                <EFFDATE>
                    <HD>DATES:</HD>
                    <P>This act is effective on September 9, 1956</P>
                </EFFDATE>
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
        amended_label = ('DESIGNATE', p_list, destination)

        subpart_changes = build.process_designate_subpart(amended_label)

        self.assertEqual(['200-1-a', '200-1-b'], subpart_changes.keys())

        for p, change in subpart_changes.items():
            self.assertEqual(change['destination'], ['205', 'Subpart', 'A'])
            self.assertEqual(change['op'], 'assign')

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
            self.assertEqual(change['op'], 'assign')

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
        self.assertTrue(
            changes['text'].startswith(u'(b) This part carries out.\n'))

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

        self.assertEqual(changes['105-Subpart-B']['node_type'], 'subpart')

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

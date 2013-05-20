from lxml import etree
from parser.notice import *
from unittest import TestCase

class NoticeTest(TestCase):

    def test_find_section_by_section(self):
        sxs_xml = """
            <HD SOURCE="HD2">Sub Section</HD>
            <P>Content</P>
            <HD SOURCE="HD3">Sub sub section</HD>
            <P>Sub Sub Content</P>"""
        full_xml = """
        <ROOT>
            <SUPLINF>
                <HD SOURCE="HED">Supplementary Info</HD>
                <HD SOURCE="HD1">Stuff Here</HD>
                <P>Some Content</P>
                <HD SOURCE="HD1">X. Section-by-Section Analysis</HD>
                %s
                <HD SOURCE="HD1">Section that follows</HD>
                <P>Following Content</P>
            </SUPLINF>
        </ROOT>""" % sxs_xml

        sxs = etree.fromstring("<ROOT>" + sxs_xml + "</ROOT>")
        #   Must use text field since the nodes are not directly comparable
        sxs_texts = map(lambda el: el.text, list(sxs.xpath("/ROOT/*")))

        computed = find_section_by_section(etree.fromstring(full_xml))
        self.assertEqual(sxs_texts, map(lambda el: el.text, computed))

    def test_find_section_by_section_not_present(self):
        full_xml = """
        <ROOT>
            <SUPLINF>
                <HD SOURCE="HED">Supplementary Info</HD>
                <HD SOURCE="HD1">This is not sxs Analysis</HD>
                <P>Stuff</P>
                <P>Stuff2</P>
                <FTNT>Foot Note</FTNT>
            </SUPLINF>
        </ROOT>"""
        self.assertEqual([], find_section_by_section(etree.fromstring(
            full_xml)))

    def test_fetch_document_number(self):
        xml = """
        <ROOT>
            <CHILD />
            <CHILD>Body</CHILD>
            <CHILD>
                <FRDOC>[FR Doc. 2001-10 Filed 1-20-01; 12:52 am]</FRDOC>
            </CHILD>
            <CHILD>Body</CHILD>
        </ROOT>
        """
        self.assertEqual("2001-10",
                fetch_document_number(etree.fromstring(xml)))

    def test_fetch_docket_number(self):
        xml = """
        <ROOT>
            <CHILD />
            <CHILD>Body</CHILD>
            <CHILD>
                <DEPDOC>[Docket No. AGENCY-2008-6789]</DEPDOC>
            </CHILD>
            <CHILD>Body</CHILD>
        </ROOT>
        """
        self.assertEqual("2008-6789",
                fetch_docket_number(etree.fromstring(xml)))

    def test_fetch_simple_fields_withnorin(self):
        xml = """
        <ROOT>
            <CHILD>
                <AGENCY>Some Agency</AGENCY>
                <ACT>
                    <HD>Some Title</HD>
                    <P>Action Here</P>
                </ACT>
                <SUM>
                    <HD>Another Title</HD>
                    <P>Summary Summary</P>
                </SUM>
            </CHILD>
            <CHILD>Body</CHILD>
        </ROOT>
        """
        self.assertEqual(fetch_simple_fields(etree.fromstring(xml)), {
            'agency': 'Some Agency',
            'action': 'Action Here',
            'summary': 'Summary Summary'
        })

    def test_fetch_simple_fields_withrin(self):
        xml = """
        <ROOT>
            <CHILD>
                <RIN>RIN 2342-as213</RIN>
                <AGENCY>Some Agency</AGENCY>
                <ACT>
                    <HD>Some Title</HD>
                    <P>Action Here</P>
                </ACT>
                <SUM>
                    <HD>Another Title</HD>
                    <P>Summary Summary</P>
                </SUM>
            </CHILD>
            <CHILD>Body</CHILD>
        </ROOT>
        """
        self.assertEqual(fetch_simple_fields(etree.fromstring(xml)), {
            'rin': '2342-as213',
            'agency': 'Some Agency',
            'action': 'Action Here',
            'summary': 'Summary Summary'
        })
    
    def test_fetch_cfr_part(self):
        xml = """
        <ROOT>
            <CHILD />
            <CHILD>Body</CHILD>
            <CHILD>
                <CFR>19 CFR Part 90210</CFR>
            </CHILD>
            <CHILD>Body</CHILD>
        </ROOT>"""
        self.assertEqual("90210", fetch_cfr_part(etree.fromstring(xml)))

    def test_parse_date_sentence(self):
        self.assertEqual(('comments', '2009-01-08'), parse_date_sentence(
            'Comments must be received by January 8, 2009'))
        self.assertEqual(('comments', '2005-02-12'), parse_date_sentence(
            'Comments on the effective date must be received by '
            + 'February 12, 2005'))
        self.assertEqual(('effective', '1982-03-01'), parse_date_sentence(
            'This rule is effective on March 1, 1982'))
        self.assertEqual(('other', '1991-04-30'), parse_date_sentence(
            "More info will be available on April 30, 1991"))
        self.assertEqual(None, parse_date_sentence(
            'The rule effective on April 30, 1991 did not make sense'))

    def test_fetch_dates_no_xml_el(self):
        xml = """
        <ROOT>
            <CHILD />
            <PREAMB />
        </ROOT>"""
        self.assertEqual({}, fetch_dates(etree.fromstring(xml)))

    def test_fetch_dates_no_date_text(self):
        xml = """
        <ROOT>
            <CHILD />
            <PREAMB>
                <EFFDATE>
                    <HD>DATES: </HD>
                    <P>There are no dates for this.</P>
                </EFFDATE>
            </PREAMB>
        </ROOT>"""
        self.assertEqual({}, fetch_dates(etree.fromstring(xml)))
    
    def test_fetch_dates(self):
        xml = """
        <ROOT>
            <CHILD />
            <PREAMB>
                <EFFDATE>
                    <HD>DATES: </HD>
                    <P>We said stuff that's effective on May 9, 2005. If
                    you'd like to add comments, please do so by June 3, 1987.
                    Wait, that doesn't make sense. I mean, the comment
                    period ends on July 9, 2004. Whew. It would have been
                    more confusing if I said August 15, 2005. Right?</P>
                </EFFDATE>
            </PREAMB>
        </ROOT>"""
        self.assertEqual(fetch_dates(etree.fromstring(xml)), {
            'effective': ['2005-05-09'],
            'comments': ['1987-06-03', '2004-07-09'],
            'other': ['2005-08-15']
        })

    def test_build_section_by_section(self):
        xml = """
        <ROOT>
            <HD SOURCE="HD3">Section Header</HD>
            <P>Content 1</P>
            <P>Content 2</P>
            <HD SOURCE="HD4">Sub Section Header</HD>
            <P>Content 3</P>
            <HD SOURCE="HD4">Another</HD>
            <P>Content 4</P>
            <HD SOURCE="HD3">Next Section</HD>
            <P>Content 5</P>
        </ROOT>"""
        sxs = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = build_section_by_section(sxs, '100', 3)
        self.assertEqual(2, len(structures))
        self.assertEqual(structures[0], {
            'title': 'Section Header',
            'paragraphs': [
                'Content 1',
                'Content 2' 
                ],
            'children': [
                {
                    'title': 'Sub Section Header',
                    'paragraphs': ['Content 3'],
                    'children': []
                }, 
                {
                    'title': 'Another',
                    'paragraphs': ['Content 4'],
                    'children': []
                }]
            })
        self.assertEqual(structures[1], {
            'title': 'Next Section',
            'paragraphs': ['Content 5'],
            'children': []
            })

    def test_build_section_by_section_footnotes(self):
        """We only account for paragraph tags right now"""
        xml = """
        <ROOT>
            <HD SOURCE="HD3">Section Header</HD>
            <P>Content 1</P>
            <FTNT>Content A</FTNT>
            <P>Content 2</P>
        </ROOT>"""
        sxs = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = build_section_by_section(sxs, '100', 3)
        self.assertEqual(1, len(structures))
        self.assertEqual(structures[0], {
            'title': 'Section Header',
            'paragraphs': [
                'Content 1',
                'Content 2',
                ],
            'children': []
            })

    def test_build_section_by_section_label(self):
        """Check that labels are being added correctly"""
        xml = """
        <ROOT>
            <HD SOURCE="HD2">Section 99.3 Info</HD>
            <P>Content 1</P>
            <HD SOURCE="HD3">3(q)(4) More Info</HD>
            <P>Content 2</P>
        </ROOT>"""
        sxs = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = build_section_by_section(sxs, '99')
        self.assertEqual(1, len(structures))
        self.assertEqual(structures[0], {
            'title': 'Section 99.3 Info',
            'label': '99-3',
            'paragraphs': ['Content 1'],
            'children': [{
                'title': '3(q)(4) More Info',
                'label': '99-3-q-4',
                'paragraphs': ['Content 2'],
                'children': []
            }]
        })

    def test_split_into_ttsr(self):
        xml = """
        <ROOT>
            <HD SOURCE="HD3">Section Header</HD>
            <P>Content 1</P>
            <P>Content 2</P>
            <HD SOURCE="HD4">Sub Section Header</HD>
            <P>Content 3</P>
            <HD SOURCE="HD4">Another</HD>
            <P>Content 4</P>
            <HD SOURCE="HD3">Next Section</HD>
            <P>Content 5</P>
        </ROOT>"""
        sxs = list(etree.fromstring(xml).xpath("/ROOT/*"))
        title, text_els, sub_sects, remaining = split_into_ttsr(sxs, 3)
        self.assertEqual("Section Header", title.text)
        self.assertEqual(2, len(text_els))
        self.assertEqual("Content 1", text_els[0].text)
        self.assertEqual("Content 2", text_els[1].text)
        self.assertEqual(4, len(sub_sects))
        self.assertEqual("Sub Section Header", sub_sects[0].text)
        self.assertEqual("Content 3", sub_sects[1].text)
        self.assertEqual("Another", sub_sects[2].text)
        self.assertEqual("Content 4", sub_sects[3].text)
        self.assertEqual(2, len(remaining))
        self.assertEqual("Next Section", remaining[0].text)
        self.assertEqual("Content 5", remaining[1].text)

    def test_parse_into_label(self):
        self.assertEqual("101-22", 
                parse_into_label("Section 101.22Stuff", "101"))
        self.assertEqual("101-22-d", 
                parse_into_label("22(d) Content", "101"))
        self.assertEqual("101-22-d-5", 
                parse_into_label("22(d)(5) Content", "101"))
        self.assertEqual("101-22-d-5-x", 
                parse_into_label("22(d)(5)(x) Content", "101"))
        self.assertEqual("101-22-d-5-x-Q", 
                parse_into_label("22(d)(5)(x)(Q) Content", "101"))

        self.assertEqual(None,
                parse_into_label("Application of this rule", "101"))

    def test_build_notice(self):
        """Integration test for the building of a notice from XML"""
        xml = """
        <ROOT>
            <FRDOC>[FR Doc. 7878-111 Filed 2-3-78; 1:02 pm]</FRDOC>
            <CFR>220 CFR Part 9292</CFR>
            <RIN>RIN a231a-232q</RIN>
            <AGENCY>Agag</AGENCY>
            <ACT>
                <HD>Some Title</HD>
                <P>actact</P>
            </ACT>
            <SUM>
                <HD>Another Title</HD>
                <P>sum sum sum</P>
            </SUM>
            <SUPLINF>
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
        self.assertEqual(build_notice(etree.fromstring(xml)), {
            'document_number': '7878-111',
            'cfr_part': '9292',
            'rin': 'a231a-232q',
            'agency': 'Agag',
            'action': 'actact',
            'summary': 'sum sum sum',
            'dates': { 'effective': ['1956-09-09'] },
            'section_by_section': [{
                'title': '8(q) Words',
                'paragraphs': ['Content'],
                'children': [],
                'label': '9292-8-q'
            }]
        })

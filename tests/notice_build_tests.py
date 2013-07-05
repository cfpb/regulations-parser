from lxml import etree
from regparser.notice.build import *
from unittest import TestCase

class NoticeBuildTest(TestCase):

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
        self.assertEqual(build_notice(etree.fromstring(xml)), {
            'document_number': '7878-111',
            'cfr_part': '9292',
            'rin': 'a231a-232q',
            'agency': 'Agag',
            'action': 'actact',
            'contact': 'Extra contact info here',
            'summary': 'sum sum sum',
            'dates': { 'effective': ['1956-09-09'] },
            'addresses': { 
                'methods': [('Email', 'example@example.com')],
                'instructions': ['Extra instructions']
            },
            'section_by_section': [{
                'title': '8(q) Words',
                'paragraphs': ['Content'],
                'children': [],
                'label': '9292-8-q'
            }]
        })

    def test_build_notice_missing_fields(self):
        xml = """
        <ROOT>
            <FRDOC>[FR Doc. 7878-111 Filed 2-3-78; 1:02 pm]</FRDOC>
            <CFR>220 CFR Part 9292</CFR>
            <AGENCY>Agag</AGENCY>
            <FURINF>
                <HD>CONTACT INFO:</HD>
                <P>Extra contact info here</P>
            </FURINF>
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
            'agency': 'Agag',
            'action': 'actact',
            'contact': 'Extra contact info here',
            'summary': 'sum sum sum',
            'section_by_section': [{
                'title': '8(q) Words',
                'paragraphs': ['Content'],
                'children': [],
                'label': '9292-8-q'
            }]
        })


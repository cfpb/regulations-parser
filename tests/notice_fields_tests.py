#vim: set encoding=utf-8
from lxml import etree
from regparser.notice.fields import *
from unittest import TestCase

class NoticeFieldsTests(TestCase):

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
            <FURINF>
                <P>Contact information</P>
            </FURINF>
        </ROOT>
        """
        self.assertEqual(fetch_simple_fields(etree.fromstring(xml)), {
            'agency': 'Some Agency',
            'action': 'Action Here',
            'summary': 'Summary Summary',
            'contact': 'Contact information'

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
            <FURINF>
                <P>Contact information</P>
            </FURINF>
        </ROOT>
        """
        self.assertEqual(fetch_simple_fields(etree.fromstring(xml)), {
            'rin': '2342-as213',
            'agency': 'Some Agency',
            'action': 'Action Here',
            'summary': 'Summary Summary',
            'contact': 'Contact information'
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
        self.assertEqual(None, fetch_dates(etree.fromstring(xml)))

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
        self.assertEqual(None, fetch_dates(etree.fromstring(xml)))
    
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

    def test_fetch_addreses_none(self):
        xml = """
        <ROOT>
            <ADD>
                <HD>ADDRESSES:</HD>
            </ADD>
        </ROOT>"""
        self.assertEqual(None, fetch_addresses(etree.fromstring(xml)))
        xml = """
        <ROOT>
            <CHILD />
        </ROOT>"""
        self.assertEqual(None, fetch_addresses(etree.fromstring(xml)))

    def test_fetch_addresses(self):
        xml = """
        <ROOT>
            <ADD>
                <HD>ADDRESSES:</HD>
                <P>Here is some initial instruction.</P>
                <P><E T="03">Electronic: http://www.example.com.</E> MSG</P>
                <P>Mail: Some address here</P>
                <P>Blah Blah: Final method description</P>
                <P>And then, we have some instructions</P>
                <P>Followed by more instructions.</P>
            </ADD>
        </ROOT>"""
        self.assertEqual(fetch_addresses(etree.fromstring(xml)), {
            'intro': 'Here is some initial instruction.',
            'methods': [
                ('Electronic', 'http://www.example.com. MSG'),
                ('Mail', 'Some address here'),
                ('Blah Blah', 'Final method description')
            ],
            'instructions': [
                'And then, we have some instructions',
                'Followed by more instructions.'
            ]
        })
    
    def test_fetch_addresses_no_intro(self):
        xml = """
        <ROOT>
            <ADD>
                <P>Mail: Some address here</P>
                <P>Followed by more instructions.</P>
            </ADD>
        </ROOT>"""
        self.assertEqual(fetch_addresses(etree.fromstring(xml)), {
            'methods': [('Mail', 'Some address here')],
            'instructions': ['Followed by more instructions.']
        })

    def test_fetch_address_http(self):
        xml = """
        <ROOT>
            <ADD>
                <P>Mail:Something here</P>
                <P>Otherwise, visit http://example.com</P>
                <P>or https://example.com</P>
            </ADD>
        </ROOT>"""
        self.assertEqual(fetch_addresses(etree.fromstring(xml)), {
            'methods': [('Mail', 'Something here')],
            'instructions': [
                'Otherwise, visit http://example.com',
                'or https://example.com'
            ]
        })

    def test_fetch_address_instructions(self):
        xml = """
        <ROOT>
            <ADD>
                <P>Mail: Something something</P>
                <P>Instructions: Do these things</P>
                <P>Then do those things</P>
            </ADD>
        </ROOT>"""
        self.assertEqual(fetch_addresses(etree.fromstring(xml)), {
            'methods': [('Mail', 'Something something')],
            'instructions': ['Do these things', 'Then do those things']
        })

    def test_cleanup_address_p_bullet(self):
        xml = u"""<P>• Bullet: value</P>"""
        self.assertEqual(cleanup_address_p(etree.fromstring(xml)), 
            'Bullet: value')

    def test_cleanup_address_p_smushed_tag(self):
        xml = """<P>See<E T="03">This</E></P>"""
        self.assertEqual(cleanup_address_p(etree.fromstring(xml)),
            'See This')

    def test_cleanup_address_p_without_contents(self):
        xml = """<P>See<E /> here!</P>"""
        self.assertEqual(cleanup_address_p(etree.fromstring(xml)),
            'See here!')

    def test_cleanup_address_p_subchildren(self):
        xml = """<P>Oh<E T="03">yeah</E>man</P>"""
        self.assertEqual(cleanup_address_p(etree.fromstring(xml)),
            'Oh yeah man')


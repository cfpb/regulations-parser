# vim: set encoding=utf-8
from unittest import TestCase

from lxml import etree

from regparser.notice import dates


class NoticeDatesTests(TestCase):
    def test_parse_date_sentence(self):
        self.assertEqual(('comments', '2009-01-08'),
                         dates.parse_date_sentence(
                             'Comments must be received by January 8, 2009'))
        self.assertEqual(('comments', '2005-02-12'),
                         dates.parse_date_sentence('Comments on the effective '
                                                   'date must be received by '
                                                   'February 12, 2005'))
        self.assertEqual(('effective', '1982-03-01'),
                         dates.parse_date_sentence(
                             'This rule is effective on March 1, 1982'))
        self.assertEqual(('other', '1991-04-30'),
                         dates.parse_date_sentence(
                             "More info will be available on April 30, 1991"))
        self.assertEqual(None,
                         dates.parse_date_sentence('The rule effective on '
                                                   'April 30, 1991 did not '
                                                   'make sense'))

    def test_fetch_dates_no_xml_el(self):
        xml = """
        <ROOT>
            <CHILD />
            <PREAMB />
        </ROOT>"""
        self.assertEqual(None, dates.fetch_dates(etree.fromstring(xml)))

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
        self.assertEqual(None, dates.fetch_dates(etree.fromstring(xml)))

    def test_fetch_dates_emphasis(self):
        xml = """
        <ROOT>
            <DATES>
                <HD SOURCE="HED">DATES:</HD>
                <P>
                    <E T="03">Effective date:</E>
                    The rule is effective June 1, 2077.
                </P>
                <P>
                    <E T="03">Applicability date:</E>
                    Its requirements apply to things after that date.
                </P>
            </DATES>
        </ROOT>"""
        self.assertEqual(dates.fetch_dates(etree.fromstring(xml)), {
            'effective': ['2077-06-01']})

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
        self.assertEqual(dates.fetch_dates(etree.fromstring(xml)), {
            'effective': ['2005-05-09'],
            'comments': ['1987-06-03', '2004-07-09'],
            'other': ['2005-08-15']
        })

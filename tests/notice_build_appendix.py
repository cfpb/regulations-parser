from unittest import TestCase

from lxml import etree
from mock import patch

from regparser.notice import build_appendix
from regparser.notice.diff import Amendment


class NoticeBuildAppendixTest(TestCase):
    @patch('regparser.notice.build_appendix.process_appendix')
    def test_whole_appendix(self, process):
        xml = """
        <ROOT>
            <AMDPAR>1. Adding Appendix R and S</AMDPAR>
            <HD SOURCE="HD1">Appendix R to Part 1234</HD>
            <EXTRACT>
                <P>R1</P>
                <P>R2</P>
            </EXTRACT>
            <HD SOURCE="HD1">Appendix S to Part 1234</HD>
            <EXTRACT>
                <P>S1</P>
                <P>S2</P>
            </EXTRACT>
        </ROOT>"""
        xml = etree.fromstring(xml)

        build_appendix.whole_appendix(xml, '1234', 'S')
        self.assertEqual(process.call_count, 1)
        extract = process.call_args[0][0]
        self.assertEqual(['Appendix S to Part 1234', 'S1', 'S2'],
                         [n.text for n in extract])

        build_appendix.whole_appendix(xml, '1234', 'R')
        self.assertEqual(process.call_count, 2)
        extract = process.call_args[0][0]
        self.assertEqual(['Appendix R to Part 1234', 'R1', 'R2'],
                         [n.text for n in extract])

    @patch('regparser.notice.build_appendix.whole_appendix')
    def test_parse_appendix_changes(self, whole):
        amends = [Amendment('POST', '111-Appendix:A'),
                  Amendment('POST', '111-Appendix:A'),
                  Amendment('PUT', '111-Appendix:B-12'),
                  Amendment('PUT', '111-Appendix:D'),
                  Amendment('PUT', '111-Appendix:E-12-b')]

        build_appendix.parse_appendix_changes(amends, '1234', 'XML')
        self.assertEqual(3, whole.call_count)

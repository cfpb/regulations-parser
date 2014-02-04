#vim: set encoding=utf-8
from unittest import TestCase

from lxml import etree
from mock import patch

from regparser.notice import build_interp
from regparser.notice.diff import Amendment


class NoticeBuildInterpTest(TestCase):
    @patch('regparser.notice.build_interp.interpretations')
    def test_process_with_headers(self, interpretations):
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
            build_interp.process_with_headers('111', etree.fromstring(xml_str))
            root, nodes = interpretations.parse_from_xml.call_args[0]
            self.assertEqual(root.label, ['111', 'Interp'])
            self.assertEqual(['HD', 'T1', 'P'], [n.tag for n in nodes])

    def test_process_without_headers(self):
        xml = """
            <REGTEXT>
                <AMDPAR>Adding comment 33(c)-5, 34(b)-5, and 34(b)-6</AMDPAR>
                <P>5. five five five</P>
                <P>i. eye eye eye</P>
                <P>5. five five five2</P>
                <P>6. six six six</P>
            </REGTEXT>"""
        amended_labels = [Amendment('POST', '111-Interpretations-33-(c)-5'),
                          Amendment('POST', '111-Interpretations-34-(b)-5'),
                          Amendment('POST', '111-Interpretations-34-(b)-6')]
        interp = build_interp.process_without_headers(
            '111', etree.fromstring(xml), amended_labels)
        self.assertEqual(2, len(interp.children))
        c, b = interp.children
        self.assertEqual(c.label, ['111', '33', 'c', 'Interp'])
        self.assertEqual(1, len(c.children))
        c5 = c.children[0]
        self.assertEqual('5. five five five', c5.text.strip())
        self.assertEqual(c5.label, ['111', '33', 'c', 'Interp', '5'])
        self.assertEqual(1, len(c5.children))
        c5i = c5.children[0]
        self.assertEqual('i. eye eye eye', c5i.text.strip())
        self.assertEqual(c5i.label, ['111', '33', 'c', 'Interp', '5', 'i'])
        self.assertEqual([], c5i.children)

        b5, b6 = b.children
        self.assertEqual('5. five five five2', b5.text.strip())
        self.assertEqual(b5.label, ['111', '34', 'b', 'Interp', '5'])
        self.assertEqual([], b5.children)
        self.assertEqual('6. six six six', b6.text.strip())
        self.assertEqual(b6.label, ['111', '34', 'b', 'Interp', '6'])
        self.assertEqual([], b6.children)

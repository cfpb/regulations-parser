#vim: set encoding=utf-8
from unittest import TestCase

from lxml import etree
from mock import patch

from regparser.notice import build_interp


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


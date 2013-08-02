#vim: set encoding=utf-8
from unittest import TestCase

from lxml import etree

from regparser.tree.xml_parser.reg_text import *

class RegTextTest(TestCase):

    def test_build_section_intro_text(self):
        xml = u"""
            <SECTION>
                <SECTNO>§ 8675.309</SECTNO>
                <SUBJECT>Definitions.</SUBJECT>
                <P>Some content about this section.</P>
                <P>(a) something something</P>
            </SECTION>
        """
        node = build_section('8675', etree.fromstring(xml))
        self.assertEqual('Some content about this section.', node.text.strip())
        self.assertEqual(1, len(node.children))
        self.assertEqual(['8675', '309'], node.label)

        child = node.children[0]
        self.assertEqual('(a) something something', child.text.strip())
        self.assertEqual([], child.children)
        self.assertEqual(['8675', '309', 'a'], child.label)

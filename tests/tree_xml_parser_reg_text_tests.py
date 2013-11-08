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

    def test_build_section_collapsed_level(self):
        xml = u"""
            <SECTION>
                <SECTNO>§ 8675.309</SECTNO>
                <SUBJECT>Definitions.</SUBJECT>
                <P>(a) <E T="03">Transfers </E>—(1) <E T="03">Notice.</E> follow
                </P>
            </SECTION>
        """
        node = build_section('8675', etree.fromstring(xml))
        self.assertEqual(node.label, ['8675', '309'])
        self.assertEqual(
            [c.label for c in node.children], [['8675', '309', 'a']])

        lowest_label = node.children[0].children[0].label
        self.assertEqual(['8675', '309', 'a', '1'], lowest_label)

    def test_get_title(self):
        xml = u"""
            <PART>
                <HD>regulation title</HD>
            </PART>"""
        title = get_title(etree.fromstring(xml))
        self.assertEqual(u'regulation title', title)

    def test_get_reg_part(self):
        xml = u"""
            <PART>
                <EAR> Pt. 204 </EAR>
            </PART>
        """
        part = get_reg_part(etree.fromstring(xml))
        self.assertEqual(part, '204')

    def test_get_reg_part_fr_notice_style(self):
        xml = u"""
            <REGTEXT PART="204">
            <SECTION>
            </SECTION>
            </REGTEXT>
        """
        part = get_reg_part(etree.fromstring(xml))
        self.assertEqual(part, '204')

    def test_get_subpart_title(self):
        xml = u"""
            <SUBPART>
                <HD>Subpart A—First subpart</HD>
            </SUBPART>"""
        subpart_title = get_subpart_title(etree.fromstring(xml))
        self.assertEqual(subpart_title, u'Subpart A—First subpart')

    def test_build_subpart(self):
        xml = u"""
            <SUBPART>
                <HD>Subpart A—First subpart</HD>
            <SECTION>
                <SECTNO>§ 8675.309</SECTNO>
                <SUBJECT>Definitions.</SUBJECT>
                <P>Some content about this section.</P>
                <P>(a) something something</P>
            </SECTION>
            <SECTION>
                <SECTNO>§ 8675.310 </SECTNO>
                <SUBJECT>Definitions.</SUBJECT>
                <P>Some content about this section.</P>
                <P>(a) something something</P>
            </SECTION>
            </SUBPART>
        """
        subpart = build_subpart('8675', etree.fromstring(xml))
        self.assertEqual(subpart.node_type, 'subpart')
        self.assertEqual(len(subpart.children), 2)
        self.assertEqual(subpart.label, ['8675', 'Subpart', 'A'])
        child_labels = [c.label for c in subpart.children]
        self.assertEqual([['8675', '309'], ['8675', '310']], child_labels)

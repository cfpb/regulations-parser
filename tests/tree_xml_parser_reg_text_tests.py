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

    def test_build_section_reserved(self):
        xml = u"""
            <SECTION>
                <SECTNO>§ 8675.309</SECTNO>
                <RESERVED>[Reserved]</RESERVED>
            </SECTION>"""
        node = build_section('8675', etree.fromstring(xml))
        self.assertEqual(node.label, ['8675', '309'])
        self.assertEqual(u'§ 8675.309 [Reserved]', node.title)
        self.assertEqual([], node.children)

    def test_build_section_ambiguous(self):
        xml = u"""
            <SECTION>
                <SECTNO>§ 8675.309</SECTNO>
                <SUBJECT>Definitions.</SUBJECT>
                <P>(g) Some Content</P>
                <P>(h) H Starts</P>
                <P>(1) H-1</P>
                <P>(2) H-2</P>
                <P>(i) Is this 8675-309-h-2-i or 8675-309-i</P>
                <P>%s</P>
            </SECTION>
        """
        n8675_309 = build_section('8675', etree.fromstring(xml % '(ii) A'))
        n8675_309_h = n8675_309.children[1]
        n8675_309_h_2 = n8675_309_h.children[1]
        self.assertEqual(2, len(n8675_309.children))
        self.assertEqual(2, len(n8675_309_h.children))
        self.assertEqual(2, len(n8675_309_h_2.children))

        n8675_309 = build_section('8675', etree.fromstring(xml % '(A) B'))
        n8675_309_h = n8675_309.children[1]
        n8675_309_h_2 = n8675_309_h.children[1]
        n8675_309_h_2_i = n8675_309_h_2.children[0]
        self.assertEqual(2, len(n8675_309.children))
        self.assertEqual(2, len(n8675_309_h.children))
        self.assertEqual(1, len(n8675_309_h_2.children))
        self.assertEqual(1, len(n8675_309_h_2_i.children))

        n8675_309 = build_section('8675', etree.fromstring(xml % '(1) C'))
        self.assertEqual(3, len(n8675_309.children))

        n8675_309 = build_section('8675', etree.fromstring(xml % '(3) D'))
        n8675_309_h = n8675_309.children[1]
        n8675_309_h_2 = n8675_309_h.children[1]
        self.assertEqual(2, len(n8675_309.children))
        self.assertEqual(3, len(n8675_309_h.children))
        self.assertEqual(1, len(n8675_309_h_2.children))

    def test_build_section_collapsed(self):
        xml = u"""
            <SECTION>
                <SECTNO>§ 8675.309</SECTNO>
                <SUBJECT>Definitions.</SUBJECT>
                <P>(a) aaa</P>
                <P>(1) 111</P>
                <P>(2) 222—(i) iii. (A) AAA</P>
                <P>(B) BBB></P>
            </SECTION>
        """
        n309 = build_section('8675', etree.fromstring(xml))
        self.assertEqual(1, len(n309.children))
        n309_a = n309.children[0]
        self.assertEqual(2, len(n309_a.children))
        n309_a_2 = n309_a.children[1]
        self.assertEqual(1, len(n309_a_2.children))
        n309_a_2_i = n309_a_2.children[0]
        self.assertEqual(2, len(n309_a_2_i.children))

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

    def test_get_markers(self):
        text = u'(a) <E T="03">Transfer </E>—(1) <E T="03">Notice.</E> follow'
        markers = get_markers(text)
        self.assertEqual(markers, [u'a', u'1'])

    def test_get_markers_and_text(self):
        text = u'(a) <E T="03">Transfer </E>—(1) <E T="03">Notice.</E> follow'
        wrap = '<P>%s</P>' % text

        doc = etree.fromstring(wrap)
        markers = get_markers(text)
        result = get_markers_and_text(doc, markers)

        markers = [r[0] for r in result]
        self.assertEqual(markers, [u'a', u'1'])

        text = [r[1][0] for r in result]
        self.assertEqual(text, [u'(a) Transfer —', u'(1) Notice. follow'])

        tagged = [r[1][1] for r in result]
        self.assertEqual(
            tagged,
            [u'(a) <E T="03">Transfer </E>—', u'(1) <E T="03">Notice.</E> follow'])

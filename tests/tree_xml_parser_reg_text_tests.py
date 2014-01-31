#vim: set encoding=utf-8
from unittest import TestCase

from lxml import etree
from mock import patch

from regparser.tree.xml_parser.reg_text import *


class RegTextTest(TestCase):
    def test_build_from_section_intro_text(self):
        xml = u"""
            <SECTION>
                <SECTNO>§ 8675.309</SECTNO>
                <SUBJECT>Definitions.</SUBJECT>
                <P>Some content about this section.</P>
                <P>(a) something something</P>
            </SECTION>
        """
        node = build_from_section('8675', etree.fromstring(xml))[0]
        self.assertEqual('Some content about this section.', node.text.strip())
        self.assertEqual(1, len(node.children))
        self.assertEqual(['8675', '309'], node.label)

        child = node.children[0]
        self.assertEqual('(a) something something', child.text.strip())
        self.assertEqual([], child.children)
        self.assertEqual(['8675', '309', 'a'], child.label)

    def test_build_from_section_collapsed_level(self):
        xml = u"""
        <SECTION>
            <SECTNO>§ 8675.309</SECTNO>
            <SUBJECT>Definitions.</SUBJECT>
            <P>(a) <E T="03">Transfers </E>—(1) <E T="03">Notice.</E> follow
            </P>
            <P>(b) <E T="03">Contents</E> (1) Here</P>
        </SECTION>
        """
        node = build_from_section('8675', etree.fromstring(xml))[0]
        self.assertEqual(node.label, ['8675', '309'])
        self.assertEqual(2, len(node.children))
        self.assertEqual(node.children[0].label, ['8675', '309', 'a'])
        self.assertEqual(node.children[1].label, ['8675', '309', 'b'])

        a1_label = node.children[0].children[0].label
        self.assertEqual(['8675', '309', 'a', '1'], a1_label)

        self.assertEqual(1, len(node.children[1].children))

    def test_build_from_section_collapsed_level_emph(self):
        xml = u"""
            <SECTION>
                <SECTNO>§ 8675.309</SECTNO>
                <SUBJECT>Definitions.</SUBJECT>
                <P>(a) aaaa</P>
                <P>(1) 1111</P>
                <P>(i) iiii</P>
                <P>(A) AAA—(<E T="03">1</E>) eeee</P>
            </SECTION>
        """
        node = build_from_section('8675', etree.fromstring(xml))[0]
        a1iA = node.children[0].children[0].children[0].children[0]
        self.assertEqual(u"(A) AAA—", a1iA.text)
        self.assertEqual(1, len(a1iA.children))
        self.assertEqual("(1) eeee", a1iA.children[0].text.strip())

    def test_build_from_section_double_collapsed(self):
        xml = u"""
            <SECTION>
                <SECTNO>§ 8675.309</SECTNO>
                <SUBJECT>Definitions.</SUBJECT>
                <P>(a) <E T="03">Keyterm</E>—(1)(i) Content</P>
                <P>(ii) Content2</P>
            </SECTION>
        """
        node = build_from_section('8675', etree.fromstring(xml))[0]
        self.assertEqual(['8675', '309'], node.label)
        self.assertEqual(1, len(node.children))

        a = node.children[0]
        self.assertEqual(['8675', '309', 'a'], a.label)
        self.assertEqual(1, len(a.children))

        a1 = a.children[0]
        self.assertEqual(['8675', '309', 'a', '1'], a1.label)
        self.assertEqual(2, len(a1.children))

        a1i, a1ii = a1.children
        self.assertEqual(['8675', '309', 'a', '1', 'i'], a1i.label)
        self.assertEqual(['8675', '309', 'a', '1', 'ii'], a1ii.label)

    def test_build_from_section_reserved(self):
        xml = u"""
            <SECTION>
                <SECTNO>§ 8675.309</SECTNO>
                <RESERVED>[Reserved]</RESERVED>
            </SECTION>"""
        node = build_from_section('8675', etree.fromstring(xml))[0]
        self.assertEqual(node.label, ['8675', '309'])
        self.assertEqual(u'§ 8675.309 [Reserved]', node.title)
        self.assertEqual([], node.children)

    def test_build_from_section_reserved_range(self):
        xml = u"""
            <SECTION>
                <SECTNO>§§ 8675.309-8675.311</SECTNO>
                <RESERVED>[Reserved]</RESERVED>
            </SECTION>"""
        n309, n310, n311 = build_from_section('8675', etree.fromstring(xml))
        self.assertEqual(n309.label, ['8675', '309'])
        self.assertEqual(n310.label, ['8675', '310'])
        self.assertEqual(n311.label, ['8675', '311'])
        self.assertEqual(u'§ 8675.309 [Reserved]', n309.title)
        self.assertEqual(u'§ 8675.310 [Reserved]', n310.title)
        self.assertEqual(u'§ 8675.311 [Reserved]', n311.title)

    def test_build_from_section_ambiguous(self):
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
        n8675_309 = build_from_section('8675',
                                       etree.fromstring(xml % '(ii) A'))[0]
        n8675_309_h = n8675_309.children[1]
        n8675_309_h_2 = n8675_309_h.children[1]
        self.assertEqual(2, len(n8675_309.children))
        self.assertEqual(2, len(n8675_309_h.children))
        self.assertEqual(2, len(n8675_309_h_2.children))

        n8675_309 = build_from_section('8675',
                                       etree.fromstring(xml % '(A) B'))[0]
        n8675_309_h = n8675_309.children[1]
        n8675_309_h_2 = n8675_309_h.children[1]
        n8675_309_h_2_i = n8675_309_h_2.children[0]
        self.assertEqual(2, len(n8675_309.children))
        self.assertEqual(2, len(n8675_309_h.children))
        self.assertEqual(1, len(n8675_309_h_2.children))
        self.assertEqual(1, len(n8675_309_h_2_i.children))

        n8675_309 = build_from_section('8675',
                                       etree.fromstring(xml % '(1) C'))[0]
        self.assertEqual(3, len(n8675_309.children))

        n8675_309 = build_from_section('8675',
                                       etree.fromstring(xml % '(3) D'))[0]
        n8675_309_h = n8675_309.children[1]
        n8675_309_h_2 = n8675_309_h.children[1]
        self.assertEqual(2, len(n8675_309.children))
        self.assertEqual(3, len(n8675_309_h.children))
        self.assertEqual(1, len(n8675_309_h_2.children))

    def test_build_from_section_collapsed(self):
        xml = u"""
            <SECTION>
                <SECTNO>§ 8675.309</SECTNO>
                <SUBJECT>Definitions.</SUBJECT>
                <P>(a) aaa</P>
                <P>(1) 111</P>
                <P>(2) 222—(i) iii. (A) AAA</P>
                <P>(B) BBB</P>
            </SECTION>
        """
        n309 = build_from_section('8675', etree.fromstring(xml))[0]
        self.assertEqual(1, len(n309.children))
        n309_a = n309.children[0]
        self.assertEqual(2, len(n309_a.children))
        n309_a_2 = n309_a.children[1]
        self.assertEqual(1, len(n309_a_2.children))
        n309_a_2_i = n309_a_2.children[0]
        self.assertEqual(2, len(n309_a_2_i.children))

    def test_build_from_section_italic_levels(self):
        xml = u"""
            <SECTION>
                <SECTNO>§ 8675.309</SECTNO>
                <SUBJECT>Definitions.</SUBJECT>
                <P>(a) aaa</P>
                <P>(1) 111</P>
                <P>(i) iii</P>
                <P>(A) AAA</P>
                <P>(<E T="03">1</E>) i1i1i1</P>
            </SECTION>
        """
        node = build_from_section('8675', etree.fromstring(xml))[0]
        self.assertEqual(1, len(node.children))
        self.assertEqual(node.label, ['8675', '309'])

        node = node.children[0]
        self.assertEqual(node.label, ['8675', '309', 'a'])
        self.assertEqual(1, len(node.children))

        node = node.children[0]
        self.assertEqual(node.label, ['8675', '309', 'a', '1'])
        self.assertEqual(1, len(node.children))

        node = node.children[0]
        self.assertEqual(node.label, ['8675', '309', 'a', '1', 'i'])
        self.assertEqual(1, len(node.children))

        node = node.children[0]
        self.assertEqual(node.label, ['8675', '309', 'a', '1', 'i', 'A'])
        self.assertEqual(1, len(node.children))

        node = node.children[0]
        self.assertEqual(node.label, ['8675', '309', 'a', '1', 'i', 'A', '1'])

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
            [u'(a) <E T="03">Transfer </E>—',
             u'(1) <E T="03">Notice.</E> follow'])

    def test_get_markers_and_text_emph(self):
        text = '(A) aaaa. (<E T="03">1</E>) 1111'
        xml = etree.fromstring('<P>%s</P>' % text)
        markers = get_markers(text)
        result = get_markers_and_text(xml, markers)

        a, a1 = result
        self.assertEqual(('A', ('(A) aaaa. ', '(A) aaaa. ')), a)
        self.assertEqual(('<E T="03">1</E>', ('(1) 1111',
                                              '(<E T="03">1</E>) 1111')), a1)

    def test_get_markers_bad_citation(self):
        text = '(vi)<E T="03">Keyterm.</E>The information required by '
        text += 'paragraphs (a)(2), (a)(4)(iii), (a)(5), (b) through (d), '
        text += '(f), and (g) with respect to something, (i), (j), (l) '
        text += 'through (p), (q)(1), and (r) with respect to something.'
        self.assertEqual(['vi'], get_markers(text))

    @patch('regparser.tree.xml_parser.reg_text.content')
    def test_preprocess_xml(self, content):
        xml = etree.fromstring("""
        <CFRGRANULE>
          <PART>
            <APPENDIX>
              <TAG>Other Text</TAG>
              <GPH DEEP="453" SPAN="2">
                <GID>ABCD.0123</GID>
              </GPH>
            </APPENDIX>
          </PART>
        </CFRGRANULE>""")
        content.Macros.return_value = [
            ("//GID[./text()='ABCD.0123']/..", """
              <HD SOURCE="HD1">Some Title</HD>
              <GPH DEEP="453" SPAN="2">
                <GID>EFGH.0123</GID>
              </GPH>""")]
        preprocess_xml(xml)
        should_be = etree.fromstring("""
        <CFRGRANULE>
          <PART>
            <APPENDIX>
              <TAG>Other Text</TAG>
              <HD SOURCE="HD1">Some Title</HD>
              <GPH DEEP="453" SPAN="2">
                <GID>EFGH.0123</GID>
              </GPH></APPENDIX>
          </PART>
        </CFRGRANULE>""")

        self.assertEqual(etree.tostring(xml), etree.tostring(should_be))

    def test_next_marker_stars(self):
        xml = etree.fromstring("""
            <ROOT>
                <P>(i) Content</P>
                <STARS />
                <P>(xi) More</P>
            </ROOT>""")
        self.assertEqual('xi', next_marker(xml.getchildren()[0], []))

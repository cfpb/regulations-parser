# vim: set encoding=utf-8
from unittest import TestCase
from lxml import etree

from regparser.tree.xml_parser import interpretations, tree_utils


class InterpretationsTest(TestCase):
    def test_interpretation_markers(self):
        text = '1. Kiwis and Mangos'
        marker = interpretations.get_first_interp_marker(text)
        self.assertEqual(marker, '1')

    def test_interpretation_markers_roman(self):
        text = 'iv. Kiwis and Mangos'
        marker = interpretations.get_first_interp_marker(text)
        self.assertEqual(marker, 'iv')

    def test_interpretation_markers_emph(self):
        text = '<E T="03">1.</E> Kiwis and Mangos'
        marker = interpretations.get_first_interp_marker(text)
        self.assertEqual(marker, '<E T="03">1</E>')

        text = '<E T="03">1. Kiwis and Mangos.</E> More content.'
        marker = interpretations.get_first_interp_marker(text)
        self.assertEqual(marker, '<E T="03">1</E>')

    def test_interpretation_markers_stars_no_period(self):
        for marker in ('4 ', 'iv  ', 'A\t'):
            text = marker + '* * *'
            found_marker = interpretations.get_first_interp_marker(text)
            self.assertEqual(marker.strip(), found_marker)

            text = "33 * * * Some more stuff"
            found_marker = interpretations.get_first_interp_marker(text)
            self.assertEqual(None, found_marker)

    def test_interpretation_markers_parenthesis(self):
        text = u'(b) Some text here.'
        found_marker = interpretations.get_first_interp_marker(text)
        self.assertEqual("b", found_marker)

    def test_build_supplement_tree(self):
        """Integration test"""
        xml = """<APPENDIX>
            <HD SOURCE="HED">
                Supplement I to Part 737-Official Interpretations</HD>
            <HD SOURCE="HD2">Section 737.5 NASCAR</HD>
            <P>1. Paragraph 1</P>
            <P>i. Paragraph i; A. Start of A</P>
            <HD SOURCE="HD2">5(a) Access Device</HD>
            <P>1. Paragraph 111</P>
            <P>i. Content content</P>
            <P>ii. More content</P>
            <P>A. Aaaaah</P>
            <P><E T="03">1.</E> More info</P>
            <P><E T="03">2.</E> Second info</P>
            <P><E T="03">3. Keyterms</E></P>
        </APPENDIX>"""
        tree = interpretations.build_supplement_tree('737',
                                                     etree.fromstring(xml))
        self.assertEqual(['737', 'Interp'], tree.label)
        self.assertEqual(1, len(tree.children))

        i5 = tree.children[0]
        self.assertEqual(['737', '5', 'Interp'], i5.label)
        self.assertEqual(2, len(i5.children))

        i51, i5a = i5.children
        self.assertEqual(['737', '5', 'Interp', '1'], i51.label)
        self.assertEqual(1, len(i51.children))
        i51i = i51.children[0]
        self.assertEqual(['737', '5', 'Interp', '1', 'i'], i51i.label)
        self.assertEqual(1, len(i51i.children))
        i51iA = i51i.children[0]
        self.assertEqual(['737', '5', 'Interp', '1', 'i', 'A'], i51iA.label)
        self.assertEqual(0, len(i51iA.children))

        self.assertEqual(['737', '5', 'a', 'Interp'], i5a.label)
        self.assertEqual(1, len(i5a.children))
        i5a1 = i5a.children[0]
        self.assertEqual(['737', '5', 'a', 'Interp', '1'], i5a1.label)
        self.assertEqual(2, len(i5a1.children))
        i5a1i, i5a1ii = i5a1.children
        self.assertEqual(['737', '5', 'a', 'Interp', '1', 'i'], i5a1i.label)
        self.assertEqual(0, len(i5a1i.children))

        self.assertEqual(['737', '5', 'a', 'Interp', '1', 'ii'], i5a1ii.label)
        self.assertEqual(1, len(i5a1ii.children))
        i5a1iiA = i5a1ii.children[0]
        self.assertEqual(['737', '5', 'a', 'Interp', '1', 'ii', 'A'],
                         i5a1iiA.label)
        self.assertEqual(3, len(i5a1iiA.children))
        i5a1iiA1, i5a1iiA2, i5a1iiA3 = i5a1iiA.children
        self.assertEqual(['737', '5', 'a', 'Interp', '1', 'ii', 'A', '1'],
                         i5a1iiA1.label)
        self.assertEqual(i5a1iiA1.tagged_text, '<E T="03">1.</E> More info')
        self.assertEqual(0, len(i5a1iiA1.children))
        self.assertEqual(['737', '5', 'a', 'Interp', '1', 'ii', 'A', '2'],
                         i5a1iiA2.label)
        self.assertEqual(i5a1iiA2.tagged_text, '<E T="03">2.</E> Second info')
        self.assertEqual(0, len(i5a1iiA2.children))
        self.assertEqual(['737', '5', 'a', 'Interp', '1', 'ii', 'A', '3'],
                         i5a1iiA3.label)
        self.assertEqual(i5a1iiA3.tagged_text, '<E T="03">3. Keyterms</E>')
        self.assertEqual(0, len(i5a1iiA3.children))

    def test_build_supplement_tree_spacing(self):
        """Integration test"""
        xml = """<APPENDIX>
            <HD SOURCE="HED">
                Supplement I to Part 737-Official Interpretations</HD>
            <HD SOURCE="HD2">Section 737.5 NASCAR</HD>
            <P>1.<E T="03">Phrase</E>. More Content</P>
            <P>i. I like<PRTPAGE />ice cream</P>
            <P>A. Aaaaah</P>
            <P><E T="03">1.</E>More info</P>
        </APPENDIX>"""
        tree = interpretations.build_supplement_tree('737',
                                                     etree.fromstring(xml))
        self.assertEqual(['737', 'Interp'], tree.label)
        self.assertEqual(1, len(tree.children))

        s5 = tree.children[0]
        self.assertEqual(1, len(s5.children))

        s51 = s5.children[0]
        self.assertEqual(s51.text.strip(), "1. Phrase. More Content")
        self.assertEqual(1, len(s51.children))

        s51i = s51.children[0]
        self.assertEqual(s51i.text.strip(), "i. I like ice cream")
        self.assertEqual(1, len(s51i.children))

        s51iA = s51i.children[0]
        self.assertEqual(s51iA.text.strip(), "A. Aaaaah")
        self.assertEqual(1, len(s51iA.children))

        s51iA1 = s51iA.children[0]
        self.assertEqual(s51iA1.text.strip(), "1. More info")
        self.assertEqual(0, len(s51iA1.children))

    def test_build_supplement_tree_repeats(self):
        """Integration test"""
        xml = """<APPENDIX>
            <HD SOURCE="HED">
                Supplement I to Part 737-Official Interpretations</HD>
            <HD SOURCE="HD2">Appendices G and H-Content</HD>
            <P>1. G:H</P>
            <HD SOURCE="HD2">Appendix G</HD>
            <P>1. G</P>
            <HD SOURCE="HD2">Appendix H</HD>
            <P>1. H</P>
        </APPENDIX>"""
        tree = interpretations.build_supplement_tree('737',
                                                     etree.fromstring(xml))
        self.assertEqual(['737', 'Interp'], tree.label)
        self.assertEqual(3, len(tree.children))
        aGH, aG, aH = tree.children

        self.assertEqual(['737', 'G_H', 'Interp'], aGH.label)
        self.assertEqual(['737', 'G', 'Interp'], aG.label)
        self.assertEqual(['737', 'H', 'Interp'], aH.label)

    def test_build_supplement_tree_skip_levels(self):
        xml = """<APPENDIX>
            <HD SOURCE="HED">
                Supplement I to Part 737-Official Interpretations</HD>
            <HD SOURCE="HD2">Section 737.5 NASCAR</HD>
            <HD SOURCE="HD2">5(a)(1)(i) Access Device</HD>
            <P>1. Paragraph 111</P>
            <HD SOURCE="HD2">5(b) Other Devices</HD>
            <P>1. Paragraph 222</P>
        </APPENDIX>"""
        tree = interpretations.build_supplement_tree('737',
                                                     etree.fromstring(xml))
        self.assertEqual(['737', 'Interp'], tree.label)
        self.assertEqual(1, len(tree.children))

        i5 = tree.children[0]
        self.assertEqual(['737', '5', 'Interp'], i5.label)
        self.assertEqual(2, len(i5.children))
        i5a, i5b = i5.children

        self.assertEqual(['737', '5', 'a', 'Interp'], i5a.label)
        self.assertEqual(1, len(i5a.children))
        i5a1 = i5a.children[0]

        self.assertEqual(['737', '5', 'a', '1', 'Interp'], i5a1.label)
        self.assertEqual(1, len(i5a1.children))
        i5a1i = i5a1.children[0]

        self.assertEqual(['737', '5', 'a', '1', 'i', 'Interp'], i5a1i.label)
        self.assertEqual(1, len(i5a1i.children))

        self.assertEqual(['737', '5', 'b', 'Interp'], i5b.label)
        self.assertEqual(1, len(i5b.children))

    def test_build_supplement_tree_appendix_paragraphs(self):
        xml = """<APPENDIX>
            <HD SOURCE="HED">
                Supplement I to Part 737-Official Interpretations</HD>
            <HD SOURCE="HD2">Appendix H</HD>
            <HD SOURCE="HD3">(b) bbbbbbb</HD>
            <P>1. Paragraph b</P>
            <HD SOURCE="HD3">(b)(5) b5b5b5</HD>
            <P>1. Paragraph b5</P>
        </APPENDIX>"""
        tree = interpretations.build_supplement_tree('737',
                                                     etree.fromstring(xml))
        self.assertEqual(['737', 'Interp'], tree.label)
        self.assertEqual(1, len(tree.children))

        iH = tree.children[0]
        self.assertEqual(['737', 'H', 'Interp'], iH.label)
        self.assertEqual(1, len(iH.children))

        iHb = iH.children[0]
        self.assertEqual(['737', 'H', 'b', 'Interp'], iHb.label)
        self.assertEqual(2, len(iHb.children))

        iHb1, iHb5 = iHb.children
        self.assertEqual(['737', 'H', 'b', 'Interp', '1'], iHb1.label)
        self.assertEqual(['737', 'H', 'b', '5', 'Interp'], iHb5.label)

    def test_build_supplement_intro_section(self):
        """Integration test"""
        xml = """<APPENDIX>
            <HD SOURCE="HED">
                Supplement I to Part 737-Official Interpretations</HD>
            <HD SOURCE="HD1">Introduction</HD>
            <P>1. Some content. (a) Badly named</P>
            <P>(b) Badly named</P>
            <HD SOURCE="HD1">Subpart A</HD>
            <HD SOURCE="HD2">Section 737.13</HD>
            <P><E>13(a) Some Stuff!</E></P>
            <P>1. 131313</P>
            <HD SOURCE="HD2">Appendix G</HD>
            <P>1. G</P>
        </APPENDIX>"""
        tree = interpretations.build_supplement_tree('737',
                                                     etree.fromstring(xml))
        self.assertEqual(['737', 'Interp'], tree.label)
        self.assertEqual(3, len(tree.children))
        h1, s13, g = tree.children

        self.assertEqual(['737', 'Interp', 'h1'], h1.label)
        self.assertEqual(['737', '13', 'Interp'], s13.label)
        self.assertEqual(['737', 'G', 'Interp'], g.label)

        self.assertEqual(len(h1.children), 2)
        self.assertEqual('1. Some content. (a) Badly named',
                         h1.children[0].text.strip())
        self.assertEqual('(b) Badly named',
                         h1.children[1].text.strip())
        self.assertEqual(len(h1.children[0].children), 0)

        self.assertEqual(1, len(s13.children))
        self.assertEqual('13(a) Some Stuff!', s13.children[0].title)

    def test_process_inner_child(self):
        xml = """
        <ROOT>
            <HD>Title</HD>
            <P>1. 111. i. iii</P>
            <STARS />
            <P>A. AAA</P>
            <P><E T="03">1.</E> eee</P>
        </ROOT>"""
        node = etree.fromstring(xml).xpath('//HD')[0]
        stack = tree_utils.NodeStack()
        interpretations.process_inner_children(stack, node)
        while stack.size() > 1:
            stack.unwind()
        n1 = stack.m_stack[0][0][1]
        self.assertEqual(['1'], n1.label)
        self.assertEqual(1, len(n1.children))

        n1i = n1.children[0]
        self.assertEqual(['1', 'i'], n1i.label)
        self.assertEqual(n1i.text.strip(), 'i. iii')
        self.assertEqual(1, len(n1i.children))

        n1iA = n1i.children[0]
        self.assertEqual(['1', 'i', 'A'], n1iA.label)
        self.assertEqual(1, len(n1iA.children))

        n1iA1 = n1iA.children[0]
        self.assertEqual(['1', 'i', 'A', '1'], n1iA1.label)
        self.assertEqual(0, len(n1iA1.children))

    def test_process_inner_child_space(self):
        xml = """
        <ROOT>
            <HD>Title</HD>
            <P>1. 111</P>
            <P>i. See country A. Not that country</P>
        </ROOT>"""
        node = etree.fromstring(xml).xpath('//HD')[0]
        stack = tree_utils.NodeStack()
        interpretations.process_inner_children(stack, node)
        while stack.size() > 1:
            stack.unwind()
        n1 = stack.m_stack[0][0][1]
        self.assertEqual(['1'], n1.label)
        self.assertEqual(1, len(n1.children))

        n1i = n1.children[0]
        self.assertEqual(['1', 'i'], n1i.label)
        self.assertEqual(0, len(n1i.children))

    def test_process_inner_child_incorrect_xml(self):
        xml = """
        <ROOT>
            <HD>Title</HD>
            <P><E T="03">1.</E> 111</P>
            <P>i. iii</P>
            <P><E T="03">2.</E> 222 Incorrect Content</P>
        </ROOT>"""
        node = etree.fromstring(xml).xpath('//HD')[0]
        stack = tree_utils.NodeStack()
        interpretations.process_inner_children(stack, node)
        while stack.size() > 1:
            stack.unwind()
        self.assertEqual(2, len(stack.m_stack[0]))

    def test_process_inner_child_no_marker(self):
        xml = """
            <ROOT>
                <HD>Title</HD>
                <P>1. 111</P>
                <P>i. iii</P>
                <P>Howdy Howdy</P>
            </ROOT>"""
        node = etree.fromstring(xml).xpath('//HD')[0]
        stack = tree_utils.NodeStack()
        interpretations.process_inner_children(stack, node)
        while stack.size() > 1:
            stack.unwind()
        i1 = stack.m_stack[0][0][1]
        self.assertEqual(1, len(i1.children))
        i1i = i1.children[0]
        self.assertEqual(0, len(i1i.children))
        self.assertEqual(i1i.text.strip(), "i. iii\n\nHowdy Howdy")

    def test_process_inner_child_depth_spec(self):
        xml = """
            <ROOT>
                <HD>Title</HD>
                <P depth="1">1. 111</P>
                <P depth="2">i. iii</P>
                <P depth="1">Howdy Howdy</P>
            </ROOT>"""
        node = etree.fromstring(xml).xpath('//HD')[0]
        stack = tree_utils.NodeStack()
        interpretations.process_inner_children(stack, node)
        while stack.size() > 1:
            stack.unwind()
        i1 = stack.m_stack[0][0][1]
        i2 = stack.m_stack[0][1][1]
        self.assertEqual(1, len(i1.children))
        i1i = i1.children[0]
        self.assertEqual(0, len(i1i.children))
        self.assertEqual(i1i.text.strip(), "i. iii")
        self.assertEqual(i2.text.strip(), "Howdy Howdy")

    def test_process_inner_child_has_citation(self):
        xml = """
        <ROOT>
            <HD>Title</HD>
            <P>1. Something something see comment 22(a)-2.i. please</P>
        </ROOT>"""
        node = etree.fromstring(xml).xpath('//HD')[0]
        stack = tree_utils.NodeStack()
        interpretations.process_inner_children(stack, node)
        while stack.size() > 1:
            stack.unwind()
        tree = stack.m_stack[0][0][1]
        self.assertEqual(0, len(tree.children))

    def test_process_inner_child_stars_and_inline(self):
        xml = """
        <ROOT>
            <HD>Title</HD>
            <STARS />
            <P>2. Content. * * *</P>
            <STARS />
            <P>xi. Content</P>
            <STARS />
        </ROOT>"""
        node = etree.fromstring(xml).xpath('//HD')[0]
        stack = tree_utils.NodeStack()
        interpretations.process_inner_children(stack, node)
        while stack.size() > 1:
            stack.unwind()
        tree = stack.m_stack[0][0][1]
        self.assertEqual(['2'], tree.label)
        self.assertEqual(1, len(tree.children))
        self.assertEqual(['2', 'xi'], tree.children[0].label)
        self.assertEqual(0, len(tree.children[0].children))

    def test_process_inner_child_collapsed_i(self):
        xml = """
        <ROOT>
            <HD>Title</HD>
            <P>1. <E T="03">Keyterm text</E> i. Content content</P>
            <P>ii. Other stuff</P>
        </ROOT>"""
        node = etree.fromstring(xml).xpath('//HD')[0]
        stack = tree_utils.NodeStack()
        interpretations.process_inner_children(stack, node)
        while stack.size() > 1:
            stack.unwind()
        tree = stack.m_stack[0][0][1]
        self.assertEqual(['1'], tree.label)
        self.assertEqual(2, len(tree.children))
        self.assertEqual(['1', 'i'], tree.children[0].label)
        self.assertEqual(0, len(tree.children[0].children))
        self.assertEqual(['1', 'ii'], tree.children[1].label)
        self.assertEqual(0, len(tree.children[1].children))

    def test_is_title(self):
        titles = [
            "<HD SOURCE='HD1'>Some Title</HD>",
            "<HD SOURCE='HD2'>Some Title</HD>",
            "<P><E T='03'>Section 111.22</E></P>",
            "<P><E T='03'>21(b) Contents</E>.</P>",
            "<P>31(r) Contents.</P>",
            "<P>Section 111.31 Contents.</P>",
            "<P>Paragraph 51(b)(1)(i).</P>",
        ]
        for title in titles:
            self.assertTrue(interpretations.is_title(etree.fromstring(title)))

        non_titles = [
            "<HD SOURCE='HED'>Some Header</HD>",
            "<IMG>Some Image</IMG>",
            "<P>Then Section 22.111</P>",
            "<P><E T='03'>Section 222.33</E> More text</P>",
            "<P><E T='03'>Keyterm.</E> More text</P>",
        ]
        for non_title in non_titles:
            self.assertFalse(
                interpretations.is_title(etree.fromstring(non_title)))

    def test_collapsed_markers_matches(self):
        self.assertEqual(['i'], map(
            lambda m: m.group(1),
            interpretations.collapsed_markers_matches(
                '1. AAA - i. More', '1. AAA - i. More')))
        self.assertEqual(['1'], map(
            lambda m: m.group(1),
            interpretations.collapsed_markers_matches(
                'A. AAA: 1. More', 'A. AAA: <E T="03">1</E>. More')))
        for txt in ("1. Content - i.e. More content",
                    u"1. Stuff in quotes like, “N.A.”",
                    u"i. References appendix D, part I.A.1. Stuff"
                    "A. AAA - 1. More, without tags"):
            self.assertEqual([], interpretations.collapsed_markers_matches(
                txt, txt))

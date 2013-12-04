#vim: set encoding=utf-8
from unittest import TestCase
from lxml import etree
from lxml import html

from regparser.tree.node_stack import NodeStack
from regparser.tree.xml_parser import appendices, tree_utils


class AppendicesTest(TestCase):
    def test_interpretation_markers(self):
        text = '1. Kiwis and Mangos'
        marker = appendices.get_first_interp_marker(text)
        self.assertEqual(marker, '1')

    def test_interpretation_markers_roman(self):
        text = 'iv. Kiwis and Mangos'
        marker = appendices.get_first_interp_marker(text)
        self.assertEqual(marker, 'iv')

    def test_interpretation_markers_emph(self):
        text = '<E T="03">1.</E> Kiwis and Mangos'
        marker = appendices.get_first_interp_marker(text)
        self.assertEqual(marker, '<E T="03">1')

        text = '<E T="03">1. Kiwis and Mangos.</E> More content.'
        marker = appendices.get_first_interp_marker(text)
        self.assertEqual(marker, '<E T="03">1')

    def test_interpretation_markers_none(self):
        text = '(iv) Kiwis and Mangos'
        marker = appendices.get_first_interp_marker(text)
        self.assertEqual(marker, None)

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
        tree = appendices.build_supplement_tree('737', etree.fromstring(xml))
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
        self.assertEqual(0, len(i5a1iiA1.children))
        self.assertEqual(['737', '5', 'a', 'Interp', '1', 'ii', 'A', '2'],
                         i5a1iiA2.label)
        self.assertEqual(0, len(i5a1iiA2.children))
        self.assertEqual(['737', '5', 'a', 'Interp', '1', 'ii', 'A', '3'],
                         i5a1iiA3.label)
        self.assertEqual(0, len(i5a1iiA3.children))

    def test_process_appendix_supplement(self):
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, Supp. I</EAR>
            <HD SOURCE="HED">
                Supplement I to Part 1111—Official Interpretations</HD>
            <P>Content</P>
        </APPENDIX>
        """
        self.assertEqual(appendices.process_appendix(etree.fromstring(xml),
                                                     1111), None)

    def test_process_appendix(self):
        """Integration test for appendices"""
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <P>Intro text</P>
            <HD SOURCE="HD1">Header 1</HD>
            <P>Content H1-1</P>
            <P>Content H1-2</P>
            <HD SOURCE="HD2">Subheader</HD>
            <P>Subheader content</P>
            <HD SOURCE="HD1">Header <E T="03">2</E></HD>
            <P>Final <E T="03">Content</E></P>
            <GPH>
                <PRTPAGE P="650" />
                <GID>MYGID</GID>
            </GPH>
        </APPENDIX>
        """
        appendix = appendices.process_appendix(etree.fromstring(xml), 1111)
        self.assertEqual(3, len(appendix.children))
        intro, h1, h2 = appendix.children

        self.assertEqual([], intro.children)
        self.assertEqual("Intro text", intro.text.strip())

        self.assertEqual(3, len(h1.children))
        self.assertEqual('Header 1', h1.title)
        c1, c2, sub = h1.children
        self.assertEqual([], c1.children)
        self.assertEqual('Content H1-1', c1.text.strip())
        self.assertEqual([], c2.children)
        self.assertEqual('Content H1-2', c2.text.strip())

        self.assertEqual(1, len(sub.children))
        self.assertEqual('Subheader', sub.title)
        self.assertEqual('Subheader content', sub.children[0].text.strip())

        self.assertEqual(2, len(h2.children))
        self.assertEqual('Header 2', h2.title)
        self.assertEqual('Final Content', h2.children[0].text.strip())
        self.assertEqual('![](MYGID)', h2.children[1].text.strip())

    def test_process_inner_child(self):
        xml = """
        <ROOT>
            <HD>Title</HD>
            <P>1. 111. i. iii</P>
            <P>A. AAA</P>
            <P><E T="03">1.</E> eee</P>
        </ROOT>"""
        node = etree.fromstring(xml).xpath('//HD')[0]
        stack = NodeStack()
        appendices.process_inner_children(stack, node)
        while stack.size() > 1:
            tree_utils.unwind_stack(stack)
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
        self.assertEqual(['1', 'i', 'A', '<E T="03">1'], n1iA1.label)
        self.assertEqual(0, len(n1iA1.children))

    def test_process_inner_child_space(self):
        xml = """
        <ROOT>
            <HD>Title</HD>
            <P>1. 111</P>
            <P>i. See country A. Not that country</P>
        </ROOT>"""
        node = etree.fromstring(xml).xpath('//HD')[0]
        stack = NodeStack()
        appendices.process_inner_children(stack, node)
        while stack.size() > 1:
            tree_utils.unwind_stack(stack)
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
            <P>1. 111</P>
            <P>i. iii</P>
            <P><E T="03">2. 222</E> Incorrect Content</P>
        </ROOT>"""
        node = etree.fromstring(xml).xpath('//HD')[0]
        stack = NodeStack()
        appendices.process_inner_children(stack, node)
        while stack.size() > 1:
            tree_utils.unwind_stack(stack)
        self.assertEqual(2, len(stack.m_stack[0]))

    def test_interpretation_level(self):
        self.assertEqual(3, appendices.interpretation_level('1'))
        self.assertEqual(4, appendices.interpretation_level('ii'))
        self.assertEqual(5, appendices.interpretation_level('C'))
        self.assertEqual(6, appendices.interpretation_level('<E T="03">1'))
        self.assertEqual(3, appendices.interpretation_level('1', 2))
        self.assertEqual(4, appendices.interpretation_level('ii', 3))
        self.assertEqual(5, appendices.interpretation_level('C', 4))
        #   Unlikely that the level jumped from 3 to 5
        self.assertEqual(3, appendices.interpretation_level('<E T="03">2', 3))

    def test_is_title(self):
        titles = [
            "<HD SOURCE='HD1'>Some Title</HD>",
            "<HD SOURCE='HD2'>Some Title</HD>",
            "<P><E T='03'>Section 111.22</E></P>",
        ]
        for title in titles:
            self.assertTrue(appendices.is_title(etree.fromstring(title)))

        non_titles = [
            "<HD SOURCE='HED'>Some Header</HD>",
            "<IMG>Some Image</IMG>",
            "<P>Section 22.111</P>",
            "<P><E T='03'>Section 222.33</E> More text</P>",
            "<P><E T='03'>Keyterm.</E> More text</P>",
        ]
        for non_title in non_titles:
            self.assertFalse(appendices.is_title(etree.fromstring(non_title)))

#vim: set encoding=utf-8
from unittest import TestCase
from lxml import etree
from lxml import html

from regparser.tree.node_stack import NodeStack
from regparser.tree.xml_parser import appendices

class AppendicesTest(TestCase):
    def test_interpretation_markers(self):
        text = '1. Kiwis and Mangos'
        marker = appendices.get_interpretation_markers(text)
        self.assertEqual(marker, '1')

    def test_interpretation_markers_roman(self):
        text = 'iv. Kiwis and Mangos'
        marker = appendices.get_interpretation_markers(text)
        self.assertEqual(marker, 'iv')

    def test_interpretation_markers_none(self):
        text = '(iv) Kiwis and Mangos'
        marker = appendices.get_interpretation_markers(text)
        self.assertEqual(marker, None)

    def test_supplement_letter(self):
        text = u'Supplement J to Part 204'
        letter = appendices.get_supplement_letter(text, 204)
        self.assertEqual('J', letter)

    def test_supplement_letter_none(self):
        text = 'Supplement K'
        letter = appendices.get_supplement_letter(text, 204)
        self.assertEqual(letter, None)

    def test_appendix_section_number(self):
        text = u'A-13 A Very Nice Appendix.'
        number = appendices.get_appendix_section_number(text, 'A')
        self.assertEqual('13', number)

    def test_appendix_section_number_none(self):
        text = u'A Very Nice Appendix.'
        number = appendices.get_appendix_section_number(text, 'A')
        self.assertEqual(None, number)

    def test_process_supplement_header(self):
        xml = """
                <HD>Section 737.5 NASCAR</HD>
        """
        node = html.fragment_fromstring(xml, create_parent='DIV')
        m_stack = NodeStack()
        m_stack.push_last((1, None))
        appendices.process_supplement(737, m_stack ,node)

        last = m_stack.pop()
        self.assertEqual(last[0][0], 2)
        self.assertEqual(last[0][1].label, ['5'])

    def test_process_supplement_header(self):
        xml = """
                <HD>2(a) Access Device</HD>
        """
        node = html.fragment_fromstring(xml, create_parent='DIV')
        m_stack = NodeStack()
        m_stack.push_last((1, None))
        appendices.process_supplement(737, m_stack ,node)

        last = m_stack.pop()
        self.assertEqual(last[0][0], 2)
        self.assertEqual(last[0][1].label, ['2(a)'])
        self.assertEqual(last[0][1].title, '2(a) Access Device')

    def test_process_supplement_header(self):
        xml = """
                <P>i. The red panda escaped.</P>"""
        node = html.fragment_fromstring(xml, create_parent='DIV')
        m_stack = NodeStack()
        m_stack.push_last((1, None))
        appendices.process_supplement(737, m_stack ,node)

        last = m_stack.pop()
        self.assertEqual(last[0][0], 4)
        self.assertEqual(last[0][1].label, ['i'])
        self.assertEqual(last[0][1].text, 'i. The red panda escaped.')

    def test_appendix_tag_supplement(self):
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, Supp. I</EAR>
            <HD SOURCE="HED">Supplement I to Part 1111—Official Interpretations</HD>
            <P>Content</P>
        </APPENDIX>
        """
        self.assertEqual(appendices.appendix_tag(etree.fromstring(xml), 1111),
                         None)

    def test_appendix_tag(self):
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
            <HD SOURCE="HD1">Header 2</HD>
            <P>Final Content</P>
        </APPENDIX>
        """
        appendix = appendices.appendix_tag(etree.fromstring(xml), 1111)
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

        self.assertEqual(1, len(h2.children))
        self.assertEqual('Header 2', h2.title)
        self.assertEqual('Final Content', h2.children[0].text.strip())

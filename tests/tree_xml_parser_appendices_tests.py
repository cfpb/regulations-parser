#vim: set encoding=utf-8
from unittest import TestCase
from lxml import etree
from lxml import html

from reg_parser.tree.node_stack import NodeStack
from reg_parser.tree.xml_parser import appendices

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
        self.assertEqual(last[0][1]['label']['parts'], ['5'])

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
        self.assertEqual(last[0][1]['label']['parts'], ['2(a)'])
        self.assertEqual(last[0][1]['label']['title'], '2(a) Access Device')

    def test_process_supplement_header(self):
        xml = """
                <P>i. The red panda escaped.</P>
        """
        node = html.fragment_fromstring(xml, create_parent='DIV')
        m_stack = NodeStack()
        m_stack.push_last((1, None))
        appendices.process_supplement(737, m_stack ,node)

        last = m_stack.pop()
        self.assertEqual(last[0][0], 4)
        self.assertEqual(last[0][1]['label']['parts'], ['i'])
        self.assertEqual(last[0][1]['text'], 'i. The red panda escaped.')

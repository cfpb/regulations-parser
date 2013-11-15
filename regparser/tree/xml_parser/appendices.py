import itertools
import re
import string
import HTMLParser
from lxml import etree
from pyparsing import Optional, Word, LineStart, Suppress

from regparser.grammar.interpretation_headers import parser as headers
from regparser.tree.interpretation import text_to_label
from regparser.tree.node_stack import NodeStack
from regparser.tree.struct import Node
from regparser.tree.xml_parser import tree_utils
from regparser.utils import roman_nums

p_levels = [
    #0 -> A (Level 1)
    list(string.ascii_uppercase),
    #1 -> 1 (Level 2)
    [str(i) for i in range(1, 51)],
    #2 -> a (Level 3)
    list(string.ascii_lowercase),
    #3 -> 1 (Level 4)
    [str(i) for i in range(1, 51)],
    #4 -> (i)
    list(itertools.islice(roman_nums(), 0, 50)),
]

i_levels = [
    list(string.ascii_uppercase),
    [str(i) for i in range(1, 51)],
    list(itertools.islice(roman_nums(), 0, 50)),
    list(string.ascii_uppercase),
]


def get_interpretation_markers(text):
    roman_dec = Word("ivxlcdm")
    upper_dec = Word(string.ascii_uppercase)

    marker_parser = LineStart() + (
        Word(string.digits) | roman_dec | upper_dec) + Suppress(".")

    for citation, start, end in marker_parser.scanString(text):
        return citation[0]


def interpretation_level(marker):
    """
        Based on the marker, determine the interpretation paragraph level.
        Levels 1,2 don't need this, since they are marked differently.
    """
    if marker in i_levels[1]:
        #digits
        return 3
    elif marker in i_levels[2]:
        #roman_nums
        return 4
    elif marker in i_levels[3]:
        #ascii_uppercase
        return 5


def determine_level(marker, current_level):
    """ Based on the current level and the new marker, determine
    the new paragraph level. """
    if marker in p_levels[3] and current_level > 2:
        #digits
        p_level = 4
    elif marker in p_levels[0]:
        #ascii_uppercase
        p_level = 1
    elif marker in p_levels[2]:
        #ascii_lowercase
        p_level = 3
    elif marker in p_levels[4]:
        #roman_nums
        p_level = 5
    return p_level


def get_supplement_letter(title, part):
    result = re.match(ur'Supplement ([A-Z+]) to Part %d.*$' % part, title)
    if result:
        return result.group(1)


def get_appendix_section_number(title, appendix_letter):
    result = re.match(ur'^%s-(\d+).*$' % appendix_letter, title)
    if result:
        return result.group(1)


def determine_next_section(m_stack, node_level):
    """ Sometimes, sections aren't numbered or lettered with
    the body of the text. We peek at the stack, and figure out the next
    marker. """

    last_level = m_stack.peek_last()[0]

    if node_level == last_level:
        #Get the next marker on the same level
        last_marker = m_stack.peek_last()[1].label[-1]
        last_marker_index = p_levels[node_level-1].index(str(last_marker))
        next_marker = p_levels[node_level-1][last_marker_index + 1]
        return next_marker
    if node_level > last_level:
        #Get the first marker on the next level
        return p_levels[node_level - 1][0]

        #We don't need to get the next marker on a previous
        #level because this doesn't happen.


def process_supplement(part, m_stack, child):
    """ Parse the Supplement sections and paragraphs. """
    for ch in child.getchildren():
        if ch.tag.upper() == 'HD':
            label_text = text_to_label(ch.text, part)
            n = Node(node_type=Node.INTERP, label=label_text, title=ch.text)
            node_level = 1
        elif ch.tag.upper() == 'P':
            text = ' '.join([ch.text] + [c.tail for c in ch if c.tail])
            marker = get_interpretation_markers(text)
            node_text = tree_utils.get_node_text(ch)

            n = Node(node_text, label=[marker], node_type=Node.INTERP)
            node_level = interpretation_level(marker)
        tree_utils.add_to_stack(m_stack, node_level, n)


def process_appendix(m_stack, current_section, child):
    html_parser = HTMLParser.HTMLParser()

    for ch in child.getchildren():
        if ch.tag == 'HD':
            appendix_section = get_appendix_section_number(
                ch.text, current_section)

            if appendix_section is None:
                appendix_section = determine_next_section(m_stack, 2)

            n = Node(
                node_type=Node.APPENDIX, label=[appendix_section],
                title=ch.text)

            node_level = 2
            tree_utils.add_to_stack(m_stack, node_level, n)
        if ch.tag == 'P':
            text = ' '.join([ch.text] + [c.tail for c in ch if c.tail])
            markers_list = tree_utils.get_paragraph_markers(text)

            node_text = tree_utils.get_node_text(ch)

            if len(markers_list) > 0:
                if len(markers_list) > 1:
                    actual_markers = ['(%s)' % m for m in markers_list]
                    node_text = tree_utils.split_text(
                        node_text, actual_markers)
                else:
                    node_text = [node_text]

                for m, node_text in zip(markers_list, node_text):
                    n = Node(
                        node_text, label=[str(m)], node_type=Node.APPENDIX)

                    last = m_stack.peek()
                    node_level = determine_level(m, last[0][0])

                    if m == 'i':
                        #This is bit of a hack, since we can't easily
                        #distinguish between the Roman numeral #(i) and the
                        #letter (i) to determine the level. We look ahead to
                        #help. This is not #a complete solution and we should
                        #circle back at some point.

                        next_text = ' '.join(
                            [ch.getnext().text] +
                            [c.tail for c in ch.getnext() if c.tail])

                        next_markers = tree_utils.get_paragraph_markers(
                            next_text)

                        if next_markers[0] == 'ii':
                            node_level = 5
                    tree_utils.add_to_stack(m_stack, node_level, n)
            else:
                last = m_stack.peek_last()
                last[1].text = last[1].text + '\n %s' % node_text


def build_non_reg_text(reg_xml, reg_part):
    """ This builds the tree for the non-regulation text such as Appendices
    and the Supplement section. """
    doc_root = etree.fromstring(reg_xml)

    #reg_part = int(doc_root.xpath('//REGTEXT')[0].attrib['PART'])
    last_section = doc_root.xpath('//REGTEXT/PART/SECTION[last()]')[0]

    section_type = None
    node_type = None
    current_section = None
    m_stack = NodeStack()

    for child in last_section.getchildren():
        if child.tag == 'HD':
            p_level = 1
            if 'Appendix' in child.text and 'Part' in child.text:
                section_type = 'APPENDIX'
                node_type = Node.APPENDIX
                current_section = headers.parseString(child.text).letter
            elif 'Supplement' in child.text and 'Part' in child.text:
                section_type = 'SUPPLEMENT'
                node_type = Node.INTERP
            else:
                p_level = 2
                if section_type == 'SUPPLEMENT' and 'Appendix' in child.text:
                    current_section = headers.parseString(child.text).letter
                else:
                    current_section = determine_next_section(m_stack, p_level)

            if p_level == 1:
                label = [str(reg_part), current_section]
            else:
                label = [current_section]

            n = Node(node_type=node_type, label=label, title=child.text)
            last = m_stack.peek()

            if len(last) == 0:
                m_stack.push_last((p_level, n))
            else:
                tree_utils.add_to_stack(m_stack, p_level, n)
        elif current_section and section_type == 'APPENDIX':
            if child.tag == 'EXTRACT':
                process_appendix(m_stack, current_section, child)
                tree_utils.unwind_stack(m_stack)
        elif current_section and section_type == 'SUPPLEMENT':
            if child.tag == 'EXTRACT':
                process_supplement(reg_part, m_stack, child)
                tree_utils.unwind_stack(m_stack)

    while m_stack.size() > 1:
        tree_utils.unwind_stack(m_stack)

    sections = []
    for level, section in m_stack.m_stack[0]:
        sections.append(section)

    return sections

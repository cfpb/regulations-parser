import itertools
import re
import string
import HTMLParser
from lxml import etree
from pyparsing import Optional, Word, LineStart, Suppress
from parser.tree.struct import label, node
from parser.tree.appendix.carving import get_appendix_letter
from parser.tree.interpretation.carving import get_appendix_letter as get_letter
from parser.tree.interpretation.carving import get_section_number, applicable_paragraph, build_label
from parser.tree.node_stack import NodeStack

from parser.utils import roman_nums
from parser.tree.xml_parser import tree_utils

p_levels = [
    list(string.ascii_uppercase), #0 -> A (Level 1)
    [str(i) for i in range(1, 51)], #1 -> 1 (Level 2)
    list(string.ascii_lowercase),  #2 -> a (Level 3)
    [str(i) for i in range(1, 51)], #3 -> 1 (Level 4)
    list(itertools.islice(roman_nums(), 0, 50)), #4 -> (i)
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

    marker_parser = LineStart() + (Word(string.digits) | roman_dec | upper_dec) + Suppress(".")
    for citation, start, end in marker_parser.scanString(text):
        return citation[0]

def interpretation_level(marker):
    """ 
        Based on the marker, determine the interpretation paragraph level. 
        Levels 1 - 3 don't need this, since they are marked differently. 
    """
    if marker in i_levels[1]: #digits
        i_level = 4
    elif marker in i_levels[2]: #roman_nums
        i_level = 5
    elif marker in i_levels[3]: #ascii_uppercase
        i_level = 6
    return i_level

def determine_level(marker, current_level):
    """ Based on the current level and the new marker, determine 
    the new paragraph level. """
    if marker in p_levels[3] and current_level > 2: #digits
        p_level = 4
    elif marker in p_levels[0]: #ascii_uppercase
        p_level = 1
    elif marker in p_levels[2]: #ascii_lowercase
        p_level = 3
    elif marker in p_levels[4]: #roman_nums
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
        last_marker = m_stack.peek_last()[1]['label']['parts'][-1]
        last_marker_index =  p_levels[node_level-1].index(str(last_marker))
        next_marker = p_levels[node_level-1][last_marker_index + 1]
        return next_marker
    if node_level > last_level:
        #Get the first marker on the next level
        return p_levels[node_level - 1][0]

        #We don't need to get the next marker on a previous
        #level because this doesn't happen. 

def process_supplement(m_stack, child):
    supplement_section = None
    for ch in child.getchildren():
        n = None
        node_level = None
        if ch.tag == 'HD' and ch.attrib['SOURCE'] == 'HD1':
            supplement_section = get_section_number(ch.text, 1005)
            l = label(parts=[supplement_section], title=ch.text)
            n = node(children=[], label=l)
            node_level = 2
        elif ch.tag == 'HD' and ch.attrib['SOURCE'] == 'HD2':
            part_label = build_label("", applicable_paragraph(ch.text, supplement_section))
            l = label(parts=[part_label], title=ch.text)
            n = node(children=[], label=l)
            node_level = 3
        elif ch.tag == 'P':
            text = ' '.join([ch.text] + [c.tail for c in ch if c.tail])
            marker = get_interpretation_markers(text)
            node_text = tree_utils.get_node_text(ch)

            l = label(parts=[marker])
            n = node(text=node_text, children=[], label=l)
            node_level = interpretation_level(marker)

        tree_utils.add_to_stack(m_stack, node_level, n)

def process_appendix(m_stack, current_section, child):
    html_parser = HTMLParser.HTMLParser()

    for ch in child.getchildren():
        if ch.tag == 'HD':
            appendix_section = get_appendix_section_number(ch.text, current_section)

            if appendix_section is None:
                appendix_section = determine_next_section(m_stack, 2)

            l = label(parts=[appendix_section], title=ch.text)
            n = node(children=[], label=l)

            node_level = 2
            tree_utils.add_to_stack(m_stack, node_level, n)
        if ch.tag == 'P':
            text = ' '.join([ch.text] + [c.tail for c in ch if c.tail])
            markers_list = tree_utils.get_paragraph_markers(text)

            node_text = tree_utils.get_node_text(ch)

            if len(markers_list) > 0:
                if len(markers_list) > 1:
                    actual_markers = ['(%s)' % m for m in markers_list]
                    node_text = tree_utils.split_text(node_text, actual_markers)
                else:
                    node_text= [node_text]

                for m, node_text in zip(markers_list, node_text):
                    l = label(parts=[str(m)])
                    n = node(text=node_text, children=[], label=l)

                    last = m_stack.peek()
                    node_level = determine_level(m, last[0][0])

                    if m == 'i':
                        #This is bit of a hack, since we can't easily distinguish between the Roman numeral
                        #(i) and the letter (i) to determine the level. We look ahead to help. This is not 
                        #a complete solution and we should circle back at some point. 
                        next_text = ' '.join([ch.getnext().text] + [c.tail for c in ch.getnext() if c.tail])
                        next_markers = tree_utils.get_paragraph_markers(next_text)
                        if next_markers[0] == 'ii':
                            node_level = 5
                    tree_utils.add_to_stack(m_stack, node_level, n)
            else:
                last = m_stack.peek_last()
                last[1]['text'] = last[1]['text'] + '\n %s' % node_text

def build_non_reg_text(reg_xml):
    """ This builds the tree for the non-regulation text such as Appendices 
    and the Supplement section. """
    doc_root = etree.fromstring(reg_xml)

    reg_part = int(doc_root.xpath('//REGTEXT')[0].attrib['PART'])
    last_section = doc_root.xpath('//REGTEXT/PART/SECTION[last()]')[0]

    section_type = None
    current_section = None
    m_stack = NodeStack()

    for child in last_section.getchildren():
        if child.tag == 'HD':
            p_level = 1
            if 'Appendix' in child.text and 'Part' in child.text:
                section_type = 'APPENDIX'
                current_section = get_appendix_letter(child.text, reg_part)
            elif 'Supplement' in child.text and 'Part' in child.text:
                section_type = 'SUPPLEMENT'
                current_section = get_supplement_letter(child.text, reg_part)
                if current_section == 'I':
                    current_section = 'Interpretations'
            else:
                p_level = 2
                if section_type == 'SUPPLEMENT' and 'Appendix' in child.text:
                    current_section = get_letter(child.text)
                else:
                    current_section = determine_next_section(m_stack, p_level)

            if p_level == 1:
                l = label(parts=[str(reg_part), current_section], title=child.text)
            else:
                l = label(parts=[current_section], title=child.text)

            n = node(children=[], label=l)
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
                process_supplement(m_stack, child)
                tree_utils.unwind_stack(m_stack)

    while m_stack.size() > 1:
        tree_utils.unwind_stack(m_stack)

    sections = []
    for level, section in m_stack.m_stack[0]:
        sections.append(section)

    return sections

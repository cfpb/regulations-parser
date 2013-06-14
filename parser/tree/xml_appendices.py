import itertools
import re
import string
import HTMLParser
from lxml import etree
from parser.tree.struct import label, node
from parser.tree.appendix.carving import get_appendix_letter
from parser.tree.node_stack import NodeStack

from parser.utils import roman_nums
from parser.tree.xml_tree import get_paragraph_markers, split_text

p_levels = [
    list(string.ascii_uppercase), #0 -> A
    [str(i) for i in range(1, 51)], #1 -> 1
    list(string.ascii_lowercase),  #2 -> a
    [str(i) for i in range(1, 51)], #3 -> 1
    list(itertools.islice(roman_nums(), 0, 50)), #4 -> (i)
]

def determine_level(marker, current_level):
    """ Based on the current level and the new marker, determine 
    the new paragraph level. """
    if marker in p_levels[3] and current_level > 2: #digits
        p_level = 4
    if marker in p_levels[0]: #ascii_uppercase
        p_level = 1
    if marker in p_levels[2]: #ascii_lowercase
        p_level = 3
    if marker in p_levels[4]: #roman_nums
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

def prepend_parts(parts_prefix, n):
    """ Recursively preprend parts_prefix to the parts of the node 
    n. Parts is a list of markers that indicates where you are in the 
    regulation text. """
    n['label']['parts'] = parts_prefix + n['label']['parts']

    if len(n['children']) > 1:
        for c in n['children']:
            prepend_parts(parts_prefix, c)
    return n

def determine_next_section(m_stack):
    last_level = m_stack.peek_last()[0]
    return p_levels[last_level][0]

def unwind_stack(m_stack):
    children = m_stack.pop()
    parts_prefix = m_stack.peek_last()[1]['label']['parts']
    children = [prepend_parts(parts_prefix, c[1]) for c in children]
    m_stack.peek_last()[1]['children'] = children

def add_to_stack(m_stack, node_level, node):
    """ Add a new node with level node_level to the stack. Unwind the stack 
    when necessary. """

    last = m_stack.peek()
    element = (node_level, node)

    if node_level > last[0][0]:
        m_stack.push(element)
    elif node_level < last[0][0]:
        while last[0][0] > node_level:
            unwind_stack(m_stack)
            last = m_stack.peek()
        m_stack.push_last(element)
    else:
        m_stack.push_last(element)

def build_tree(reg_xml):
    doc_root = etree.fromstring(reg_xml)

    reg_part = doc_root.xpath('//REGTEXT')[0].attrib['PART']
    part = doc_root.xpath('//REGTEXT/PART')[0]

    reg_part = int(doc_root.xpath('//REGTEXT')[0].attrib['PART'])
    last_section = doc_root.xpath('//REGTEXT/PART/SECTION[last()]')[0]

    section_type = None
    current_section = None
    m_stack = NodeStack()

    html_parser = HTMLParser.HTMLParser()

    for child in last_section.getchildren():
        if child.tag == 'HD':
            p_level = 1
            if 'Appendix' in child.text and 'Part' in child.text:
                section_type = 'A'
                current_section = get_appendix_letter(child.text, reg_part)
            elif 'Supplement' in child.text and 'Part' in child.text:
                section_type = 'I'
                current_section = get_supplement_letter(child.text, reg_part)
            else:
                current_section = determine_next_section(m_stack)
                p_level = 2

            l = label(parts=[current_section], title=child.text)
            n = node(children=[], label=l)

            last = m_stack.peek()

            if len(last) == 0 or last[0][0] == p_level:
                m_stack.push_last((p_level, n))
            elif last[0][0] < p_level:
                m_stack.push((p_level, n))

        elif current_section and section_type == 'A':
            if child.tag == 'EXTRACT':
                for ch in child.getchildren():
                    if ch.tag == 'HD':
                        appendix_section = get_appendix_section_number(ch.text, current_section)
                        l = label(parts=[appendix_section], title=ch.text)
                        n = node(children=[], label=l)

                        node_level = 2
                        add_to_stack(m_stack, node_level, n)
                    if ch.tag == 'P':
                        text = ' '.join([ch.text] + [c.tail for c in ch if c.tail])
                        markers_list = get_paragraph_markers(text)
                        node_text = ' '.join([ch.text] + [etree.tostring(c) for c in ch if c.tail])
                        node_text = html_parser.unescape(node_text)

                        if len(markers_list) > 0:
                            if len(markers_list) > 1:
                                actual_markers = ['(%s)' % m for m in markers_list]
                                node_text = split_text(node_text, actual_markers)
                            else:
                                node_text= [node_text]

                            for m, node_text in zip(markers_list, node_text):
                                l = label(parts=[str(m)])
                                n = node(text=node_text, children=[], label=l)

                                last = m_stack.peek()
                                node_level  = determine_level(m, last[0][0])
                                element = (node_level, n)

                                add_to_stack(m_stack, node_level, n)
                        else:
                            last = m_stack.peek_last()
                            last[1]['text'] = last[1]['text'] + '\n %s' % node_text
                unwind_stack(m_stack)
    if m_stack.size() > 0:
        print m_stack.m_stack

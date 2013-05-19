#!/usr/bin/env python
import re
from lxml import etree
from parser.tree.struct import label, node
from parser.grammar.internal_citations import any_depth_p
from parser.tree.paragraph import p_levels
from parser.tree.node_stack import NodeStack

def get_paragraph_markers(text):
    for citation, start, end in any_depth_p.scanString(text):
        if start == 0:
            return citation[0][0]
    return []

def determine_level(c, current_level):
    """ Regulation paragraphs are hierarchical. This determines which level 
    the paragraph is at. """
    if c in p_levels[2] and current_level  > 1:
        p_level = 3
    elif c in p_levels[0]:
        p_level = 1
    elif c in p_levels[1]:
        p_level = 2
    elif c in p_levels[3]:
        p_level = 4
    return p_level

def write_parts(node):
    node['label']['text'] = '-'.join(node['label']['parts'])

    for n in node['children']:
        write_parts(n)

def prepend_parts(parts_prefix, n):
    """ Recursively preprend parts_prefix to the parts of the node 
    n. Parts is a list of markers that indicates where you are in the 
    regulation text. """
    n['label']['parts'] = parts_prefix + n['label']['parts']

    if len(n['children']) > 1:
        for c in n['children']:
            prepend_parts(parts_prefix, c)
    return n

def split_text(text, tokens):
    """ 
        Given a body of text that contains tokens, 
        splice the text along those tokens. 
    """
    starts = [text.find(t) for t in tokens]
    slices = zip(starts, starts[1:])
    texts = [text[i[0]:i[1]] for i in slices] + [text[starts[-1]:]]
    return texts

def unwind_stack(m_stack):
    children = m_stack.pop()
    parts_prefix = m_stack.peek_last()[1]['label']['parts']
    children = [prepend_parts(parts_prefix, c[1]) for c in children]
    m_stack.peek_last()[1]['children'] = children

def build_tree():
    reg_xml = '/vagrant/data/regulations/regulation/1005.xml'
    doc = etree.parse(reg_xml)

    reg_part = doc.xpath('//REGTEXT')[0].attrib['PART']

    parent = doc.xpath('//REGTEXT/PART/HD')[0]
    title = parent.text

    tree_label = label(text="", parts=[reg_part], title=title) 
    tree = node(text="", children=[], label=tree_label)

    part = doc.xpath('//REGTEXT/PART')[0]

    sections = []
    for child in part.getchildren():
        if child.tag == 'SECTION':
            p_level = 1
            m_stack = NodeStack()
            for ch in child.getchildren():
                if ch.tag == 'P':
                    text = ' '.join([ch.text] + [c.tail for c in ch if c.tail])
                    markers_list = get_paragraph_markers(text)
                    node_text = ' '.join([ch.text] + [etree.tostring(c) for c in ch if c.tail])

                    if len(markers_list) > 1:
                        actual_markers = ['(%s)' % m for m in markers_list]
                        node_text = split_text(node_text, actual_markers)
                    else:
                        node_text = [node_text]

                    for m, node_text in zip(markers_list, node_text):
                        l = label(parts=[str(m)])
                        n = node(text=node_text, children=[], label=l)

                        new_p_level = determine_level(m, p_level)
                        if new_p_level > p_level:
                            m_stack.push((new_p_level, n))
                        elif new_p_level < p_level:
                            last = m_stack.peek()
                            while last[0][0] > new_p_level:
                                unwind_stack(m_stack)
                                last = m_stack.peek()
                            m_stack.push_last((new_p_level, n))
                        else:
                            m_stack.push_last((new_p_level, n))
                        p_level = new_p_level

            section_title = child.xpath('SECTNO')[0].text + " " + child.xpath('SUBJECT')[0].text
            section_number = re.search(r'%s\.(\d+)' % reg_part, section_title).group(1)
            section_text = ' '.join([child.text] + [c.tail for c in child if c.tail])
            sect_label = label("%s-%s" % (reg_part, section_number), [reg_part, section_number], section_title)
            sect_node = node(text=section_text, children=[], label=sect_label)

            m_stack.add_to_bottom((1, sect_node))

            while m_stack.size() > 1:
                unwind_stack(m_stack)
          
            c = m_stack.pop()[0][1]
            sections.append(c)
    tree['children'] = sections
    write_parts(tree)

    return tree

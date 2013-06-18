#!/usr/bin/env python
import re
import HTMLParser
from lxml import etree
from parser.tree.struct import label, node
from parser.grammar.internal_citations import any_depth_p
from parser.tree.paragraph import p_levels
from parser.tree.node_stack import NodeStack
from parser.tree.xml_parser.appendices import build_non_reg_text
from parser.tree.xml_parser import tree_utils

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

def build_tree(reg_xml):
    doc = etree.fromstring(reg_xml)

    reg_part = doc.xpath('//REGTEXT')[0].attrib['PART']

    parent = doc.xpath('//REGTEXT/PART/HD')[0]
    title = parent.text

    tree_label = label(text="", parts=[reg_part], title=title) 
    tree = node(text="", children=[], label=tree_label)

    part = doc.xpath('//REGTEXT/PART')[0]

    html_parser = HTMLParser.HTMLParser()

    sections = []
    for child in part.getchildren():
        if child.tag == 'SECTION':
            p_level = 1
            m_stack = NodeStack()
            for ch in child.getchildren():
                if ch.tag == 'P':
                    text = ' '.join([ch.text] + [c.tail for c in ch if c.tail])
                    markers_list = tree_utils.get_paragraph_markers(text)
                    node_text = tree_utils.get_node_text(ch)

                    if len(markers_list) > 1:
                        actual_markers = ['(%s)' % m for m in markers_list]
                        node_text = tree_utils.split_text(node_text, actual_markers)
                    else:
                        node_text = [node_text]

                    for m, node_text in zip(markers_list, node_text):
                        l = label(parts=[str(m)])
                        n = node(text=node_text, children=[], label=l)

                        new_p_level = determine_level(m, p_level)
                        last = m_stack.peek()
                        if len(last) == 0:
                            m_stack.push_last((new_p_level, n))
                        else:
                            tree_utils.add_to_stack(m_stack, new_p_level, n)
                        p_level = new_p_level

            section_title = child.xpath('SECTNO')[0].text + " " + child.xpath('SUBJECT')[0].text
            section_number = re.search(r'%s\.(\d+)' % reg_part, section_title).group(1)
            section_text = ' '.join([child.text] + [c.tail for c in child if c.tail])
            sect_label = label("%s-%s" % (reg_part, section_number), [reg_part, section_number], section_title)
            sect_node = node(text=section_text, children=[], label=sect_label)

            m_stack.add_to_bottom((1, sect_node))

            while m_stack.size() > 1:
                tree_utils.unwind_stack(m_stack)
          
            c = m_stack.pop()[0][1]
            sections.append(c)

    non_reg_sections = build_non_reg_text(reg_xml)
    tree['children'] = sections
    write_parts(tree)

    return tree

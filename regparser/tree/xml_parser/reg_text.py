#!/usr/bin/env python
import re
from lxml import etree
from regparser.tree.struct import Node
from regparser.tree.paragraph import p_levels
from regparser.tree.node_stack import NodeStack
from regparser.tree.xml_parser.appendices import build_non_reg_text
from regparser.tree import reg_text
from regparser.tree.xml_parser import tree_utils


def determine_level(c, current_level):
    """ Regulation paragraphs are hierarchical. This determines which level
    the paragraph is at. """
    if c in p_levels[2] and (current_level > 1 or c not in p_levels[0]):
        p_level = 3
    elif c in p_levels[0]:
        p_level = 1
    elif c in p_levels[1]:
        p_level = 2
    elif c in p_levels[3]:
        p_level = 4
    return p_level


def get_reg_part(reg_doc):
    """
    The CFR Part number for a regulation is contained within
    an EAR tag, for a Federal Register notice it's in a REGTEXT tag. Get the
    part number of the regulation.
    """

    #FR notice
    reg_text_xml  = reg_doc.xpath('//REGTEXT')
    if reg_text_xml:
        return reg_text_xml[0].attrib['PART']

    #e-CFR XML
    reg_ear = reg_doc.xpath('//PART/EAR')
    if reg_ear:
        return reg_ear[0].text.split('Pt.')[1].strip()


def get_title(reg_doc):
    """ Extract the title of the regulation. """
    parent = reg_doc.xpath('//PART/HD')[0]
    title = parent.text
    return title


def build_tree(reg_xml):
    doc = etree.fromstring(reg_xml)

    reg_part = get_reg_part(doc)
    title = get_title(doc)

    tree = Node("", [], [reg_part], title)

    part = doc.xpath('//PART')[0]

    subpart_xmls = [c for c in part.getchildren() if c.tag == 'SUBPART']
    if len(subpart_xmls) > 0:
        subparts = [build_subpart(reg_part, s) for s in subpart_xmls]
        tree.children = subparts
    else:
        section_xmls = [c for c in part.getchildren() if c.tag == 'SECTION']
        sections = [build_section(reg_part, s) for s in section_xmls]
        empty_part = reg_text.build_empty_part(reg_part)
        empty_part.children = sections
        tree.children = [empty_part]

    return tree


def get_subpart_title(subpart_xml):
    hds = subpart_xml.xpath('./HD')
    return [hd.text for hd in hds][0]


def build_subpart(reg_part, subpart_xml):
    subpart_title = get_subpart_title(subpart_xml)
    subpart = reg_text.build_subpart(subpart_title, reg_part)

    sections = []
    for ch in subpart_xml.getchildren():
        if ch.tag == 'SECTION':
            sections.append(build_section(reg_part, ch))

    subpart.children = sections
    return subpart


def build_section(reg_part, section_xml):
    p_level = 1
    m_stack = NodeStack()
    section_texts = []
    for ch in section_xml.getchildren():
        if ch.tag == 'P':
            text = ' '.join([ch.text] + [c.tail for c in ch if c.tail])
            markers = tree_utils.get_paragraph_markers(text)
            collapsed_markers = tree_utils.get_collapsed_markers(text)
            markers_list = [m for m in markers] + [m for m in collapsed_markers]
            node_text = tree_utils.get_node_text(ch)

            if len(markers_list) > 1:
                actual_markers = ['(%s)' % m for m in markers_list]
                node_text = tree_utils.split_text(node_text, actual_markers)
            elif markers_list:
                node_text = [node_text]
            else:   # Does not contain paragraph markers
                section_texts.append(node_text)

            for m, node_text in zip(markers_list, node_text):
                n = Node(node_text, [], [str(m)])

                new_p_level = determine_level(m, p_level)
                last = m_stack.peek()
                if len(last) == 0:
                    m_stack.push_last((new_p_level, n))
                else:
                    tree_utils.add_to_stack(m_stack, new_p_level, n)
                p_level = new_p_level

    section_title = section_xml.xpath('SECTNO')[0].text
    subject_text = section_xml.xpath('SUBJECT')[0].text
    if subject_text:
        section_title += " " + subject_text

    section_number_match = re.search(r'%s\.(\d+)' % reg_part, section_title)
    #   Sometimes not reg text sections get mixed in
    if section_number_match:
        section_number = section_number_match.group(1)
        section_text = ' '.join([section_xml.text] + section_texts)
        sect_node = Node(
            section_text, label=[reg_part, section_number],
            title=section_title)

        m_stack.add_to_bottom((1, sect_node))

        while m_stack.size() > 1:
            tree_utils.unwind_stack(m_stack)

        return m_stack.pop()[0][1]

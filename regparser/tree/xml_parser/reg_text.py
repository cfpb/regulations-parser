#vim: set encoding=utf-8
import re

from lxml import etree

from regparser import content
from regparser.tree.depth import heuristics, rules, markers as mtypes
from regparser.tree.depth.derive import derive_depths
from regparser.tree.struct import Node
from regparser.tree.paragraph import p_level_of
from regparser.tree.xml_parser.appendices import build_non_reg_text
from regparser.tree import reg_text
from regparser.tree.xml_parser import tree_utils


def get_reg_part(reg_doc):
    """
    The CFR Part number for a regulation is contained within
    an EAR tag, for a Federal Register notice it's in a REGTEXT tag. Get the
    part number of the regulation.
    """

    #FR notice
    reg_text_xml = reg_doc.xpath('//REGTEXT')
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

def get_original_date(reg_doc):
    """ Extract the original date of the regulation. """
    parent = reg_doc.xpath('//FDSYS/ORIGINALDATE')[0]
    originaldate = parent.text
    return originaldate


def preprocess_xml(xml):
    """This transforms the read XML through macros. Each macro consists of
    an xpath and a replacement xml string"""
    for path, replacement in content.Macros():
        replacement = etree.fromstring('<ROOT>' + replacement + '</ROOT>')
        for node in xml.xpath(path):
            parent = node.getparent()
            idx = parent.index(node)
            parent.remove(node)
            for repl in replacement:
                parent.insert(idx, repl)
                idx += 1


def build_tree(reg_xml):
    doc = etree.fromstring(reg_xml)
    preprocess_xml(doc)

    reg_part = get_reg_part(doc)
    title = get_title(doc)
    original_date = get_original_date(doc)

    tree = Node("", [], [reg_part], title, original_date)

    part = doc.xpath('//PART')[0]

    subpart_xmls = [c for c in part.getchildren() if c.tag == 'SUBPART']
    if len(subpart_xmls) > 0:
        subparts = [build_subpart(reg_part, s) for s in subpart_xmls]
        tree.children = subparts
    else:
        section_xmls = [c for c in part.getchildren() if c.tag == 'SECTION']
        sections = []
        for section_xml in section_xmls:
            sections.extend(build_from_section(reg_part, section_xml))
        empty_part = reg_text.build_empty_part(reg_part)
        empty_part.children = sections
        tree.children = [empty_part]

    non_reg_sections = build_non_reg_text(doc, reg_part)
    tree.children += non_reg_sections

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
            sections.extend(build_from_section(reg_part, ch))

    subpart.children = sections
    return subpart


def get_markers(text):
    """ Extract all the paragraph markers from text. Do some checks on the
    collapsed markers."""
    markers = tree_utils.get_paragraph_markers(text)
    collapsed_markers = tree_utils.get_collapsed_markers(text)

    #   Check that the collapsed markers make sense (i.e. are at least one
    #   level below the initial marker)
    if markers and collapsed_markers:
        initial_marker_levels = p_level_of(markers[-1])
        final_collapsed_markers = []
        for collapsed_marker in collapsed_markers:
            collapsed_marker_levels = p_level_of(collapsed_marker)
            if any(c > f for f in initial_marker_levels
                    for c in collapsed_marker_levels):
                final_collapsed_markers.append(collapsed_marker)
        collapsed_markers = final_collapsed_markers
    markers_list = [m for m in markers] + [m for m in collapsed_markers]

    return markers_list


def get_markers_and_text(node, markers_list):
    node_text = tree_utils.get_node_text(node, add_spaces=True)
    text_with_tags = tree_utils.get_node_text_tags_preserved(node)

    if len(markers_list) > 1:
        actual_markers = ['(%s)' % m for m in markers_list]
        plain_markers = [m.replace('<E T="03">', '').replace('</E>', '')
                         for m in actual_markers]
        node_texts = tree_utils.split_text(node_text, plain_markers)
        tagged_texts = tree_utils.split_text(text_with_tags, actual_markers)
        node_text_list = zip(node_texts, tagged_texts)
    elif markers_list:
        node_text_list = [(node_text, text_with_tags)]
    return zip(markers_list, node_text_list)


def next_marker(xml_node, remaining_markers):
    """Try to determine the marker following the current xml_node. Remaining
    markers is a list of other marks *within* the xml_node. May return
    None"""
    #   More markers in this xml node
    if remaining_markers:
        return remaining_markers[0][0]

    #   Check the next xml node; skip over stars
    sib = xml_node.getnext()
    while sib is not None and sib.tag in ('STARS', 'PRTPAGE'):
        sib = sib.getnext()
    if sib is not None:
        next_text = tree_utils.get_node_text(sib)
        next_markers = get_markers(next_text)
        if next_markers:
            return next_markers[0]


def build_from_section(reg_part, section_xml):
    section_texts = []
    nodes = []
    # Collect paragraph markers and section text (intro text for the
    # section)
    for ch in filter(lambda ch: ch.tag in ('P', 'STARS'),
                     section_xml.getchildren()):
        text = tree_utils.get_node_text(ch, add_spaces=True)
        tagged_text = tree_utils.get_node_text_tags_preserved(ch)
        markers_list = get_markers(tagged_text.strip())

        if ch.tag == 'STARS':
            nodes.append(Node(label=[mtypes.STARS_TAG]))
        elif not markers_list:
            section_texts.append((text, tagged_text))
        else:
            for m, node_text in get_markers_and_text(ch, markers_list):
                n = Node(node_text[0], [], [m], source_xml=ch)
                n.tagged_text = unicode(node_text[1])
                nodes.append(n)
            if node_text[0].endswith('* * *'):
                nodes.append(Node(label=[mtypes.INLINE_STARS]))

    # Trailing stars don't matter; slightly more efficient to ignore them
    while nodes and nodes[-1].label[0] in mtypes.stars:
        nodes = nodes[:-1]

    # Use constraint programming to figure out possible depth assignments
    depths = derive_depths(
        [n.label[0] for n in nodes],
        [rules.depth_type_order([mtypes.lower, mtypes.ints, mtypes.roman,
                                 mtypes.upper, mtypes.em_ints,
                                 mtypes.em_roman])])
    m_stack = tree_utils.NodeStack()
    if depths:
        # Find the assignment which violates the least of our heuristics
        depths = heuristics.prefer_multiple_children(depths, 0.5)
        depths = sorted(depths, key=lambda d: d.weight, reverse=True)
        depths = depths[0]
        for node, par in zip(nodes, depths):
            if par.typ != mtypes.stars:
                last = m_stack.peek()
                node.label = [l.replace('<E T="03">', '').replace('</E>', '')
                              for l in node.label]
                if len(last) == 0:
                    m_stack.push_last((1 + par.depth, node))
                else:
                    m_stack.add(1 + par.depth, node)

    section_no = section_xml.xpath('SECTNO')[0].text
    subject_xml = section_xml.xpath('SUBJECT')
    if not subject_xml:
        subject_xml = section_xml.xpath('RESERVED')
    subject_text = subject_xml[0].text

    nodes = []
    section_nums = []
    for match in re.finditer(r'%s\.(\d+)' % reg_part, section_no):
        section_nums.append(int(match.group(1)))

    #  Span of section numbers
    if u'§§' == section_no[:2] and '-' in section_no:
        first, last = section_nums
        section_nums = []
        for i in range(first, last + 1):
            section_nums.append(i)

    for section_number in section_nums:
        section_number = str(section_number)
        plain_sect_texts = [s[0] for s in section_texts]
        tagged_sect_texts = [s[1] for s in section_texts]

        section_text = ' '.join([section_xml.text] + plain_sect_texts)
        tagged_section_text = ' '.join([section_xml.text] + tagged_sect_texts)
        section_title = u"§ " + reg_part + "." + section_number
        if subject_text:
            section_title += " " + subject_text

        sect_node = Node(
            section_text, label=[reg_part, section_number],
            title=section_title)
        sect_node.tagged_text = tagged_section_text

        m_stack.add_to_bottom((1, sect_node))

        while m_stack.size() > 1:
            m_stack.unwind()

        nodes.append(m_stack.pop()[0][1])

    return nodes

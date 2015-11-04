# vim: set encoding=utf-8
import re

from lxml import etree
import logging
from regparser import content
from regparser.tree.depth import heuristics, rules, markers as mtypes
from regparser.tree.depth.derive import derive_depths
from regparser.tree.struct import Node
from regparser.tree.paragraph import p_level_of
from regparser.tree.xml_parser.appendices import build_non_reg_text
from regparser.tree import reg_text
from regparser.tree.xml_parser import tree_utils
from settings import PARAGRAPH_HIERARCHY


def get_reg_part(reg_doc):
    """
    Depending on source, the CFR part number exists in different places. Fetch
    it, wherever it is.
    """

    potential_parts = []
    potential_parts.extend(
        # FR notice
        node.attrib['PART'] for node in reg_doc.xpath('//REGTEXT'))
    potential_parts.extend(
        # e-CFR XML, under PART/EAR
        node.text.replace('Pt.', '').strip()
        for node in reg_doc.xpath('//PART/EAR')
        if 'Pt.' in node.text)
    potential_parts.extend(
        # e-CFR XML, under FDSYS/HEADING
        node.text.replace('PART', '').strip()
        for node in reg_doc.xpath('//FDSYS/HEADING')
        if 'PART' in node.text)
    potential_parts.extend(
        # e-CFR XML, under FDSYS/GRANULENUM
        node.text.strip() for node in reg_doc.xpath('//FDSYS/GRANULENUM'))
    potential_parts = [p for p in potential_parts if p.strip()]

    if potential_parts:
        return potential_parts[0]


def get_title(reg_doc):
    """ Extract the title of the regulation. """
    parent = reg_doc.xpath('//PART/HD')[0]
    title = parent.text
    return title


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
    if isinstance(reg_xml, str) or isinstance(reg_xml, unicode):
        doc = etree.fromstring(reg_xml)
    else:
        doc = reg_xml
    preprocess_xml(doc)

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
    hds = subpart_xml.xpath('./HD|./RESERVED')
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


# @profile
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
    else:
        node_text_list = [('', '')]

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

    section_no = section_xml.xpath('SECTNO')[0].text
    section_no_without_marker = re.search('[0-9]+\.[0-9]+',
                                          section_no).group(0)
    subject_xml = section_xml.xpath('SUBJECT')
    if not subject_xml:
        subject_xml = section_xml.xpath('RESERVED')
    subject_text = subject_xml[0].text

    manual_hierarchy = []
    if (reg_part in PARAGRAPH_HIERARCHY
            and section_no_without_marker in PARAGRAPH_HIERARCHY[reg_part]):
        manual_hierarchy = PARAGRAPH_HIERARCHY[reg_part][
            section_no_without_marker]

    # Collect paragraph markers and section text (intro text for the
    # section)
    i = 0
    children = [ch for ch in section_xml.getchildren()
                if ch.tag in ['P', 'STARS']]
    for ch in children:
        text = tree_utils.get_node_text(ch, add_spaces=True)
        tagged_text = tree_utils.get_node_text_tags_preserved(ch)
        markers_list = get_markers(tagged_text.strip())

        # If the child has a 'DEPTH' attribute, we're in manual
        # hierarchy mode, just constructed from the XML instead of
        # specified in configuration.
        # This presumes that every child in the section has DEPTH
        # specified, if not, things will break in and around
        # derive_depths below.
        if ch.get("depth") is not None:
            manual_hierarchy.append(int(ch.get("depth")))

        if ch.tag == 'STARS':
            nodes.append(Node(label=[mtypes.STARS_TAG]))
        elif not markers_list and manual_hierarchy:
            # is this a bunch of definitions that don't have numbers next to
            # them?
            if len(nodes) > 0:
                if (subject_text.find('Definitions.') > -1
                        or nodes[-1].text.find(
                            'For the purposes of this section')):
                    # TODO: create a grammar for definitions
                    if text.find('means') > -1:
                        def_marker = text.split('means')[0].strip().split()
                        def_marker = ''.join([word[0].upper() + word[1:]
                                              for word in def_marker])
                    elif text.find('shall have the same meaning') > -1:
                        def_marker = text.split('shall')[0].strip().split()
                        def_marker = ''.join([word[0].upper() + word[1:]
                                              for word in def_marker])
                    else:
                        def_marker = 'def{0}'.format(i)
                        i += 1
                    n = Node(text, label=[def_marker], source_xml=ch)
                    n.tagged_text = tagged_text
                    nodes.append(n)
                else:
                    section_texts.append((text, tagged_text))
            else:
                if len(children) > 1:
                    def_marker = 'def{0}'.format(i)
                    n = Node(text, [], [def_marker], source_xml=ch)
                    n.tagged_text = tagged_text
                    i += 1
                    nodes.append(n)
                else:
                    # this is the only node around
                    section_texts.append((text, tagged_text))

        elif not markers_list and not manual_hierarchy:
            # No manual heirarchy specified, append to the section.
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

    m_stack = tree_utils.NodeStack()

    # Use constraint programming to figure out possible depth assignments
    if not manual_hierarchy:
        depths = derive_depths(
            [node.label[0] for node in nodes],
            [rules.depth_type_order([mtypes.lower, mtypes.ints, mtypes.roman,
                                     mtypes.upper, mtypes.em_ints,
                                     mtypes.em_roman])])

    if not manual_hierarchy and depths:
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

    elif nodes and manual_hierarchy:
        logging.warning('Using manual depth hierarchy.')
        depths = manual_hierarchy
        if len(nodes) == len(depths):
            for node, spec in zip(nodes, depths):
                if isinstance(spec, int):
                    depth = spec
                elif isinstance(spec, tuple):
                    depth, marker = spec
                    node.marker = marker
                last = m_stack.peek()
                node.label = [l.replace('<E T="03">', '').replace('</E>', '')
                              for l in node.label]
                if len(last) == 0:
                    m_stack.push_last((1 + depth, node))
                else:
                    m_stack.add(1 + depth, node)
        else:
            logging.error('Manual hierarchy length does not match node '
                          'list length! ({0} nodes but {1} provided, '
                          '{2})'.format(
                              len(nodes),
                              len(depths),
                              [x.label[0] for x in nodes]))

    elif nodes and not manual_hierarchy:
        logging.warning(
            'Could not determine depth when parsing {0}:\n{1}'.format(
                section_no_without_marker, [node.label[0] for node in nodes]))
        for node in nodes:
            last = m_stack.peek()
            node.label = [l.replace('<E T="03">', '').replace('</E>', '')
                          for l in node.label]
            if len(last) == 0:
                m_stack.push_last((3, node))
            else:
                m_stack.add(3, node)

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

        section_title = u"§ " + reg_part + "." + section_number
        if subject_text:
            section_title += " " + subject_text

        section_text = ' '.join([section_xml.text] + plain_sect_texts)
        tagged_section_text = ' '.join([section_xml.text] + tagged_sect_texts)

        sect_node = Node(section_text, label=[reg_part, section_number],
                         title=section_title)
        sect_node.tagged_text = tagged_section_text

        m_stack.add_to_bottom((1, sect_node))

        while m_stack.size() > 1:
            m_stack.unwind()

        nodes.append(m_stack.pop()[0][1])

    return nodes

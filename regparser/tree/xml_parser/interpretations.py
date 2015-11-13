# vim: set encoding=utf-8
from copy import deepcopy
import itertools
import logging
import re

from regparser.citations import Label, remove_citation_overlaps
from regparser.layer.key_terms import KeyTerms
from regparser.notice.util import spaces_then_remove
from regparser.tree.depth import heuristics, rules, markers as mtypes
from regparser.tree.depth.derive import derive_depths
from regparser.tree.interpretation import merge_labels, text_to_labels
from regparser.tree.struct import Node, treeify
from regparser.tree.xml_parser import tree_utils

from settings import PARAGRAPH_HIERARCHY

# digits
# roman
# upper
# lower
# emphasized digit
_marker = r'(' \
    + '([0-9]+)' \
    + '|([ivxlcdm]+)' \
    + '|([A-Z]+)' \
    + '|([a-be-hjkn-uw-z]+)' \
    + '|(<E[^>]*>[0-9]+)' \
    + ')'


_marker_period_regex = re.compile(
    r'^\s*'                   # line start
    + _marker
    + r'\s*\..*', re.DOTALL)  # followed by a period and then anything


_marker_parenthetical_regex = re.compile(
    r'^\s*\('                   # line start followed by a (
    + _marker
    + r'\)\s*', re.DOTALL)  # followed by a closing ) and then anything


_marker_stars_regex = re.compile(
    r'^\s*'                   # line start
    + _marker
    + r'\s+\* \* \*\s*$', re.DOTALL)  # followed by stars


def get_first_interp_marker(text):
    match = _marker_period_regex.match(text)
    if match:
        marker = text[:text.find('.')].strip()      # up to dot
        if '<' in marker:
            marker += '</E>'
        return marker

    match = _marker_parenthetical_regex.match(text)
    if match:
        # Within the parenthesis only
        return text[text.find('(')+1:text.find(')')].strip()

    match = _marker_stars_regex.match(text)
    if match:
        return text[:text.find('*')].strip()        # up to star


_first_markers = [re.compile(ur'[\.|,|;|:|\-|—]\s*(' + marker + ')\.')
                  for marker in ['i', 'A', '1']]


def collapsed_markers_matches(node_text, tagged_text):
    """Find collapsed markers, i.e. tree node paragraphs that begin within a
    single XML node, within this text. Remove citations and other false
    positives. This is pretty hacky right now -- it focuses on the plain
    text but takes cues from the tagged text. @todo: streamline logic"""
    # In addition to the regex above, keyterms are an acceptable prefix. We
    # therefore convert keyterms to satisfy the above regex
    node_for_keyterms = Node(node_text, node_type=Node.INTERP,
                             label=[get_first_interp_marker(node_text)])
    node_for_keyterms.tagged_text = tagged_text
    keyterm = KeyTerms.get_keyterm(node_for_keyterms)
    if keyterm:
        node_text = node_text.replace(keyterm, '.'*len(keyterm))

    collapsed_markers = []
    for marker in _first_markers:
        possible = ((m, m.start(), m.end())
                    for m in marker.finditer(node_text) if m.start() > 0)
        possible = remove_citation_overlaps(node_text, possible)
        # If certain characters follow, kill it
        for following in ("e.", ")", u"”", '"', "'"):
            possible = [(m, s, end) for m, s, end in possible
                        if not node_text[end:].startswith(following)]
        possible = [m for m, _, _ in possible]
        # As all "1." collapsed markers must be emphasized, run a quick
        # check to weed out some false positives
        if '<E T="03">1' not in tagged_text:
            possible = filter(lambda m: m.group(1) != '1', possible)
        collapsed_markers.extend(possible)
    return collapsed_markers


def is_title(xml_node):
    """Not all titles are created equal. Sometimes a title appears as a
    paragraph tag, mostly to add confusion."""
    if xml_node.getchildren():
        child = xml_node.getchildren()[0]
    else:
        child = None
    return bool(
        (xml_node.tag.upper() == 'HD' and xml_node.attrib['SOURCE'] != 'HED')
        or (xml_node.tag.upper() == 'P'
            and (xml_node.text is None or not xml_node.text.strip())
            and len(xml_node.getchildren()) == 1
            and (child.tail is None or not child.tail.strip(" \n\t."))
            and text_to_labels(child.text, Label(), warn=False))
        or (xml_node.tag.upper() == 'P'
            and len(xml_node.getchildren()) == 0
            and xml_node.text and not get_first_interp_marker(xml_node.text)
            and text_to_labels(xml_node.text, Label(), warn=False,
                               force_start=True)))


def process_inner_children(inner_stack, xml_node, parent=None):
    """Process the following nodes as children of this interpretation. This
    is very similar to reg_text.py:build_from_section()"""
    # manual hierarchy should work here too
    manual_hierarchy = []
    try:
        part_and_section = re.search('[0-9]+\.[0-9]+', xml_node.text).group(0)
        part, section = part_and_section.split('.')
        part_and_section += '-Interp'

        if (part in PARAGRAPH_HIERARCHY
                and part_and_section in PARAGRAPH_HIERARCHY[part]):
            manual_hierarchy = PARAGRAPH_HIERARCHY[part][part_and_section]
    except Exception:
        pass

    children = itertools.takewhile(
        lambda x: not is_title(x), xml_node.itersiblings())
    nodes = []
    for i, xml_node in enumerate(filter(lambda c: c.tag in ('P', 'STARS'),
                                        children)):
        node_text = tree_utils.get_node_text(xml_node, add_spaces=True)
        text_with_tags = tree_utils.get_node_text_tags_preserved(xml_node)
        first_marker = get_first_interp_marker(text_with_tags)

        # If the node has a 'DEPTH' attribute, we're in manual
        # hierarchy mode, just constructed from the XML instead of
        # specified in configuration.
        # This presumes that every child in the section has DEPTH
        # specified, if not, things will break in and around
        # derive_depths below.
        if xml_node.get("depth") is not None:
            manual_hierarchy.append(int(xml_node.get("depth")))

        if xml_node.tag == 'STARS':
            nodes.append(Node(label=[mtypes.STARS_TAG]))
        elif not first_marker and nodes and manual_hierarchy:
            logging.warning("Couldn't determine interp marker. "
                            "Manual hierarchy is specified")

            n = Node(node_text, label=[str(i)], node_type=Node.INTERP)
            n.tagged_text = text_with_tags
            nodes.append(n)

        elif not first_marker and not manual_hierarchy:
            logging.warning("Couldn't determine interp marker. Appending to "
                            "previous paragraph: %s", node_text)

            if nodes:
                previous = nodes[-1]
            else:
                previous = parent

            previous.text += "\n\n" + node_text
            if hasattr(previous, 'tagged_text'):
                previous.tagged_text += "\n\n" + text_with_tags
            else:
                previous.tagged_text = text_with_tags

        else:
            collapsed = collapsed_markers_matches(node_text, text_with_tags)

            #   -2 throughout to account for matching the character + period
            ends = [m.end() - 2 for m in collapsed[1:]] + [len(node_text)]
            starts = [m.end() - 2 for m in collapsed] + [len(node_text)]

            #   Node for this paragraph
            n = Node(node_text[0:starts[0]], label=[first_marker],
                     node_type=Node.INTERP)
            n.tagged_text = text_with_tags
            nodes.append(n)
            if n.text.endswith('* * *'):
                nodes.append(Node(label=[mtypes.INLINE_STARS]))

            #   Collapsed-marker children
            for match, end in zip(collapsed, ends):
                marker = match.group(1)
                if marker == '1':
                    marker = '<E T="03">1</E>'
                n = Node(node_text[match.end() - 2:end], label=[marker],
                         node_type=Node.INTERP)
                nodes.append(n)
                if n.text.endswith('* * *'):
                    nodes.append(Node(label=[mtypes.INLINE_STARS]))

    # Trailing stars don't matter; slightly more efficient to ignore them
    while nodes and nodes[-1].label[0] in mtypes.stars:
        nodes = nodes[:-1]

    # Use constraint programming to figure out possible depth assignments
    # use manual hierarchy if it's specified
    if not manual_hierarchy:
        depths = derive_depths(
            [node.label[0] for node in nodes],
            [rules.depth_type_order([
                (mtypes.ints, mtypes.em_ints),
                (mtypes.lower, mtypes.roman, mtypes.upper),
                mtypes.upper, mtypes.em_ints, mtypes.em_roman])])

    if not manual_hierarchy and depths:
        # Find the assignment which violates the least of our heuristics
        depths = heuristics.prefer_multiple_children(depths, 0.5)
        depths = sorted(depths, key=lambda d: d.weight, reverse=True)
        depths = depths[0]
        for node, par in zip(nodes, depths):
            if par.typ != mtypes.stars:
                last = inner_stack.peek()
                node.label = [l.replace('<E T="03">', '').replace('</E>', '')
                              for l in node.label]
                if len(last) == 0:
                    inner_stack.push_last((3 + par.depth, node))
                else:
                    inner_stack.add(3 + par.depth, node)
    elif nodes and manual_hierarchy:
        logging.warning('Using manual depth hierarchy.')
        depths = manual_hierarchy
        if len(nodes) == len(depths):
            for node, depth in zip(nodes, depths):
                last = inner_stack.peek()
                node.label = [l.replace('<E T="03">', '').replace('</E>', '')
                              for l in node.label]
                if len(last) == 0:
                    inner_stack.push_last((3 + depth, node))
                else:
                    inner_stack.add(3 + depth, node)
        else:
            logging.error(
                'Manual hierarchy length does not match node list length!')

    elif nodes and not manual_hierarchy:
        logging.warning('Could not derive depth (interp):\n {}'.format(
            [node.label[0] for node in nodes]))
        # just add nodes in sequential order then
        for node in nodes:
            last = inner_stack.peek()
            node.label = [l.replace('<E T="03">', '').replace('</E>', '')
                          for l in node.label]
            if len(last) == 0:
                inner_stack.push_last((3, node))
            else:
                inner_stack.add(3, node)


def missing_levels(last_label, label):
    """Sometimes we will have a 2(a)(1) without seeing 2(a). Fill in the
    missing level"""
    #   Only care about data before 'Interp'
    label = list(itertools.takewhile(lambda l: l != Node.INTERP_MARK, label))
    #   Find only the shared segments
    zipped = zip(last_label, label)
    shared = list(itertools.takewhile(lambda pair: pair[0] == pair[1], zipped))

    missing = []
    #   Add layers in between, but do not add the last; e.g. add 2(a) but
    #   not 2(a)(1)
    for i in range(len(shared) + 1, len(label)):
        level_label = label[:i] + [Node.INTERP_MARK]
        missing.append(Node(node_type=Node.INTERP, label=level_label))
    return missing


def parse_from_xml(root, xml_nodes):
    """Core of supplement processing; shared by whole XML parsing and notice
    parsing. root is the root interpretation node (e.g. a Node with label
    '1005-Interp'). xml_nodes contains all XML nodes which will be relevant
    to the interpretations"""

    supplement_nodes = [root]

    last_label = root.label
    header_count = 0
    for ch in xml_nodes:
        node = Node(label=last_label, node_type=Node.INTERP)
        label_obj = Label.from_node(node)

        #   Explicitly ignore "subpart" headers, as they are inconsistent
        #   and they will be reconstructed as subterps client-side
        text = tree_utils.get_node_text(ch, add_spaces=True)
        if is_title(ch) and 'subpart' not in text.lower():
            labels = text_to_labels(text, label_obj)
            if labels:
                label = merge_labels(labels)
            else:   # Header without a label, like an Introduction, etc.
                header_count += 1
                label = root.label[:2] + ['h%d' % header_count]

            inner_stack = tree_utils.NodeStack()
            missing = missing_levels(last_label, label)
            supplement_nodes.extend(missing)
            last_label = label

            node = Node(node_type=Node.INTERP, label=label,
                        title=text.strip())
            inner_stack.add(2, node)

            process_inner_children(inner_stack, ch, parent=node)

            while inner_stack.size() > 1:
                inner_stack.unwind()

            ch_node = inner_stack.m_stack[0][0][1]
            supplement_nodes.append(ch_node)

    supplement_tree = treeify(supplement_nodes)

    def per_node(node):
        node.label = [l.replace('<E T="03">', '') for l in node.label]
        for child in node.children:
            per_node(child)
    for node in supplement_tree:
        per_node(node)

    return supplement_tree[0]


def build_supplement_tree(reg_part, node):
    """ Build the tree for the supplement section. """
    title = get_app_title(node)
    node = spaces_then_remove(deepcopy(node), 'PRTPAGE')
    root = Node(
        node_type=Node.INTERP,
        label=[reg_part, Node.INTERP_MARK],
        title=title)

    return parse_from_xml(root, node.getchildren())


def get_app_title(node):
    """ Appendix/Supplement sections have the title in an HD tag, or
    if they are reserved, in a <RESERVED> tag. Extract the title. """

    titles = node.xpath("./HD[@SOURCE='HED']")
    if titles:
        return titles[0].text
    else:
        return node.xpath("./RESERVED")[0]

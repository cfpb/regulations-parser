#vim: set encoding=utf-8
import itertools
import re
import string
from pyparsing import Word, LineStart, Regex, Suppress

from regparser.tree.interpretation import text_to_labels
from regparser.tree.node_stack import NodeStack
from regparser.tree.struct import Node, treeify
from regparser.tree.xml_parser import tree_utils
from regparser.utils import roman_nums


i_levels = [
    [str(i) for i in range(1, 51)],
    list(itertools.islice(roman_nums(), 0, 50)),
    list(string.ascii_uppercase),
    # We don't include the closing tag - it won't be closed if followed by a
    # key term
    ['<E T="03">' + str(i) for i in range(1, 51)],
]


def get_first_interp_marker(text):
    roman_dec = Word("ivxlcdm")
    upper_dec = Word(string.ascii_uppercase)
    emph_dec = (Regex(r"<E[^>]*>") + Word(string.digits)).setParseAction(
        lambda s, l, t: ''.join(t))

    marker_parser = LineStart() + (
        (Word(string.digits) | roman_dec | upper_dec | emph_dec)
        + Suppress("."))

    for citation, start, end in marker_parser.scanString(text):
        return citation[0]


def interpretation_level(marker, previous_level=None):
    """
        Based on the marker, determine the interpretation paragraph level.
        Levels 1,2 don't need this, since they are marked differently.
        Frustratingly, the XML is not always marked up correctly - some
        markers are sometimes italicized when they shouldn't be.
    """
    #   First, non-italics
    for idx, lst in enumerate(i_levels[:3]):
        if marker in lst:
            return idx + 3
    #   Italics don't always mean what we'd like (le sigh)
    for idx, lst in enumerate(i_levels[3:]):
        idx = idx + 3   # Shift
        if marker in lst:
            #   Probably meant non-italic...
            if previous_level is not None and idx + 3 > previous_level + 1:
                return idx
            else:
                return idx + 3


_first_markers = [re.compile(ur'[\.|,|;|-|—]\s*(' + marker + ')\.')
                  for marker in ['i', 'A']]


def interp_inner_child(child_node, stack):
    """ Build an inner child node (basically a node that's after
    -Interp- in the tree) """
    node_text = tree_utils.get_node_text(child_node)
    text_with_tags = tree_utils.get_node_text_tags_preserved(child_node)
    first_marker = get_first_interp_marker(text_with_tags)

    collapsed_markers = []
    for marker in _first_markers:
        collapsed_markers.extend(m for m in marker.finditer(node_text)
                                 if m.start() > 0)

    #   -2 throughout to account for matching the character + period
    ends = [m.end() - 2 for m in collapsed_markers[1:]] + [len(node_text)]
    starts = [m.end() - 2 for m in collapsed_markers] + [len(node_text)]

    #   Node for this paragraph
    n = Node(node_text[0:starts[0]], label=[first_marker],
             node_type=Node.INTERP)
    last = stack.peek()

    if len(last) == 0:
        stack.push_last((interpretation_level(first_marker), n))
    else:
        node_level = interpretation_level(first_marker, last[0][0])
        tree_utils.add_to_stack(stack, node_level, n)

    #   Collapsed-marker children
    for match, end in zip(collapsed_markers, ends):
        n = Node(node_text[match.end() - 2:end], label=[match.group(1)],
                 node_type=Node.INTERP)
        node_level = interpretation_level(match.group(1))
        last = stack.peek()
        if len(last) == 0:
            stack.push_last((node_level, n))
        else:
            tree_utils.add_to_stack(stack, node_level, n)


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
            and (child.tail is None or not child.tail.strip())
            and text_to_labels(child.text, '', warn=False)))


def process_inner_children(inner_stack, node):
    """Process the following nodes as children of this interpretation"""
    children = itertools.takewhile(
        lambda x: not is_title(x), node.itersiblings())
    for c in children:
        node_text = tree_utils.get_node_text(c)

        interp_inner_child(c, inner_stack)


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


def build_supplement_tree(reg_part, node):
    """ Build the tree for the supplement section. """
    m_stack = NodeStack()

    title = get_app_title(node)
    root = Node(
        node_type=Node.INTERP,
        label=[reg_part, Node.INTERP_MARK],
        title=title)

    supplement_nodes = [root]

    last_label = [reg_part, Node.INTERP_MARK]
    for ch in node:
        if is_title(ch):
            labels = text_to_labels(ch.text, reg_part)
            if not labels:
                 continue

            label = labels[0]
            inner_stack = NodeStack()
            missing = missing_levels(last_label, label)
            supplement_nodes.extend(missing)
            last_label = label

            node = Node(node_type=Node.INTERP, label=label, title=ch.text)
            tree_utils.add_to_stack(inner_stack, 2, node)

            process_inner_children(inner_stack, ch)

            while inner_stack.size() > 1:
                tree_utils.unwind_stack(inner_stack)

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


def get_app_title(node):
    """ Appendix/Supplement sections have the title in an HD tag, or
    if they are reserved, in a <RESERVED> tag. Extract the title. """

    titles = node.xpath("./HD[@SOURCE='HED']")
    if titles:
        return titles[0].text
    else:
        return node.xpath("./RESERVED")[0]

#vim: set encoding=utf-8
import copy
import itertools
import re
import string
import HTMLParser
from lxml import etree, objectify
from pyparsing import Optional, Word, LineStart, Regex, Suppress

from regparser.grammar.interpretation_headers import parser as headers
from regparser.tree.interpretation import text_to_label
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
        idx = idx + 3   #   Shift
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
    return (
        (xml_node.tag.upper() == 'HD' and xml_node.attrib['SOURCE'] != 'HED')
        or (xml_node.tag.upper() == 'P' 
            and (xml_node.text is None or not xml_node.text.strip())
            and (xml_node.tail is None or not xml_node.tail.strip())
            and len(xml_node.getchildren()) == 1 
            and text_to_label(xml_node.getchildren()[0].text, '')))



def process_inner_children(inner_stack, node):
    """Process the following nodes as children of this interpretation"""
    children = itertools.takewhile(
        lambda x: not is_title(x), node.itersiblings())
    for c in children:
        node_text = tree_utils.get_node_text(c)

        interp_inner_child(c, inner_stack)


def build_supplement_tree(reg_part, node):
    """ Build the tree for the supplement section. """
    m_stack = NodeStack()

    title = get_app_title(node)
    root = Node(
        node_type=Node.INTERP, 
        label=[reg_part, Node.INTERP_MARK], 
        title=title)

    supplement_nodes = [root]

    for ch in node:
        if is_title(ch):
            label_text = text_to_label(ch.text, reg_part)
            if not label_text:
                continue
            n = Node(node_type=Node.INTERP, label=label_text, title=ch.text)
            node_level = 1
            
            inner_stack = NodeStack()
            tree_utils.add_to_stack(inner_stack, node_level, n)

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

    return supplement_tree
    

def process_appendix(appendix, part):
    m_stack = NodeStack()

    counter = 0
    header = 0
    depth = 3
    last_hd_level = 0
    for child in appendix.getchildren():
        # escape clause for interpretations
        if (child.tag == 'HD' 
            and 'Supplement I to Part' in tree_utils.get_node_text(child)):
            break
        if ((child.tag == 'HD' and child.attrib['SOURCE'] == 'HED')
            or child.tag == 'RESERVED'):
            letter = headers.parseString(tree_utils.get_node_text(
                child)).appendix
            n = Node(node_type=Node.APPENDIX, label=[part, letter],
                    title=tree_utils.get_node_text(child).strip())
            m_stack.push_last((2, n))
            counter = 0
            depth = 3
        elif child.tag == 'HD':
            header += 1
            source = child.attrib.get('SOURCE', 'HD0')
            hd_level = int(source[2:])
            if hd_level > last_hd_level:
                depth += 1
            elif hd_level < last_hd_level:
                depth = hd_level + 3
            last_hd_level = hd_level
            n = Node(node_type=Node.APPENDIX, label=['h' + str(header)],
                     title=tree_utils.get_node_text(child).strip())
            tree_utils.add_to_stack(m_stack, depth - 1, n)
        elif child.tag == 'P' or child.tag == 'FP':
            counter += 1
            text = tree_utils.get_node_text(child)
            n = Node(text, node_type=Node.APPENDIX, label=['p' + str(counter)])
            tree_utils.add_to_stack(m_stack, depth, n)

    while m_stack.size() > 1:
        tree_utils.unwind_stack(m_stack)

    if m_stack.m_stack[0]:
        return m_stack.m_stack[0][0][1]


def get_app_title(node):
    """ Appendix/Supplement sections have the title in an HD tag, or 
    if they are reserved, in a <RESERVED> tag. Extract the title. """

    titles = node.xpath("./HD[@SOURCE='HED']")
    if titles:
        return titles[0].text
    else:
        return node.xpath("./RESERVED")[0]

    
def build_non_reg_text(reg_xml, reg_part):
    """ This builds the tree for the non-regulation text such as Appendices 
    and the Supplement section """
    doc_root = etree.fromstring(reg_xml)
    non_reg_sects = doc_root.xpath('//PART//APPENDIX')
    children = []

    for non_reg_sect in non_reg_sects:
        section_title = get_app_title(non_reg_sect)
        if 'Supplement' in section_title and 'Part' in section_title:
            children.extend(build_supplement_tree(reg_part, non_reg_sect))
        else:
            children.append(process_appendix(non_reg_sect, reg_part))

    return children

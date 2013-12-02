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

p_levels = [
    #0 -> A (Level 1)
    list(string.ascii_uppercase),
    #1 -> 1 (Level 2)
    [str(i) for i in range(1, 51)],
    #2 -> a (Level 3)
    list(string.ascii_lowercase),
    #3 -> 1 (Level 4)
    [str(i) for i in range(1, 51)],
    #4 -> (i)
    list(itertools.islice(roman_nums(), 0, 50)),
]

i_levels = [
    [str(i) for i in range(1, 51)],
    list(itertools.islice(roman_nums(), 0, 50)),
    list(string.ascii_uppercase),
    ['<E T="03">' + str(i) for i in range(1, 51)],
]


def get_interpretation_markers(text):
    roman_dec = Word("ivxlcdm")
    upper_dec = Word(string.ascii_uppercase)

    marker_parser = LineStart() + (
        ((Word(string.digits) | roman_dec | upper_dec) + Suppress("."))
        | (Regex(r"<E[^>]*>")
           + Word(string.digits)).setParseAction(lambda s, l, t: ''.join(t)))


    for citation, start, end in marker_parser.scanString(text):
        return citation[0]


def interpretation_level(marker):
    """
        Based on the marker, determine the interpretation paragraph level.
        Levels 1,2 don't need this, since they are marked differently.
    """
    for idx, lst in enumerate(i_levels):
        if marker in lst:
            return idx + 3


def determine_level(marker, current_level):
    """ Based on the current level and the new marker, determine
    the new paragraph level. """
    if marker in p_levels[3] and current_level > 2:
        #digits
        p_level = 4
    elif marker in p_levels[0]:
        #ascii_uppercase
        p_level = 1
    elif marker in p_levels[2]:
        #ascii_lowercase
        p_level = 3
    elif marker in p_levels[4]:
        #roman_nums
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
        last_marker = m_stack.peek_last()[1].label[-1]
        last_marker_index = p_levels[node_level-1].index(str(last_marker))
        next_marker = p_levels[node_level-1][last_marker_index + 1]
        return next_marker
    if node_level > last_level:
        #Get the first marker on the next level
        return p_levels[node_level - 1][0]

        #We don't need to get the next marker on a previous
        #level because this doesn't happen.


first_markers = [re.compile(ur'[\s|^|,|-|—](' + marker + ')\.')
                 for marker in ['1', 'i', 'A']]


def interp_inner_child(child_node):
    """ Build an inner child node (basically a node that's after 
    -Interp- in the tree) """
    node_text = tree_utils.get_node_text(child_node)
    text_with_tags = tree_utils.get_node_text_tags_preserved(child_node)
    first_marker = get_interpretation_markers(text_with_tags)

    collapsed_markers = []
    for marker in first_markers:
        collapsed_markers.extend(m for m in marker.finditer(node_text) 
                                 if m.start() > 0)

    m_stack = NodeStack()

    ends = [m.start() for m in collapsed_markers[1:]] + [len(node_text)]
    label = [first_marker]
    for match, end in zip(collapsed_markers, ends):
        n = Node(node_text[match.start():end], label=[match.group(1)],
                 node_type=Node.INTERP)
        node_level = interpretation_level(match.group(1))
        last = m_stack.peek()
        if len(last) == 0:
            m_stack.push_last((node_level, n))
        else:
            tree_utils.add_to_stack(m_stack, node_level, n)
        
    starts = [m.start() for m in collapsed_markers] + [len(node_text)]
    n = Node(node_text[0:starts[0]], label=[first_marker],
             node_type=Node.INTERP)
    node_level = interpretation_level(first_marker)
    m_stack.add_to_bottom((node_level, n)) 

    while m_stack.size() > 1:
        tree_utils.unwind_stack(m_stack)

    inner_root = m_stack.pop()[0][1]
    def per_node(n):
        n.label = [l.replace('<E T="03">', '') for l in n.label]
        for c in n.children:
            per_node(c)
    per_node(inner_root)

    return node_level, inner_root

    #return node_level, n


def is_title(xml_node):
    return (
        (xml_node.tag.upper() == 'HD' and xml_node.attrib['SOURCE'] != 'HED')
        or (xml_node.tag.upper() == 'P' 
            and (xml_node.text is None or not xml_node.text.strip())
            and (xml_node.tail is None or not xml_node.tail.strip())
            and len(xml_node.getchildren()) == 1 
            and text_to_label(xml_node.getchildren()[0].text, '')))



def process_inner_children(inner_stack, node):
    children = itertools.takewhile(
        lambda x: not is_title(x), node.itersiblings())
    for c in children:
        node_text = tree_utils.get_node_text(c)
        marker = get_interpretation_markers(node_text)

        node_level, n = interp_inner_child(c)
        tree_utils.add_to_stack(inner_stack, node_level, n)

    #n = Node(node_text, label=[marker], node_type=Node.INTERP)
    #node_level = interpretation_level(marker)
    #return node_level, n
        #node_level, n = interp_inner_child(c)
        #tree_utils.add_to_stack(inner_stack, node_level, n)

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

            print ">>>", ch.text
            process_inner_children(inner_stack, ch)
                
            while inner_stack.size() > 1:
                tree_utils.unwind_stack(inner_stack)

            ch_node = inner_stack.m_stack[0][0][1]
            supplement_nodes.append(ch_node)

    supplement_tree = treeify(supplement_nodes)
    return supplement_tree
    
def process_supplement(part, m_stack, child):
    """ Parse the Supplement sections and paragraphs. """
    for ch in child.getchildren():
        if ch.tag.upper() == 'HD':
            label_text = text_to_label(ch.text, part)
            n = Node(node_type=Node.INTERP, label=label_text, title=ch.text)
            node_level = 1
        elif ch.tag.upper() == 'P':
            text = ' '.join([ch.text] + [c.tail for c in ch if c.tail])
            marker = get_interpretation_markers(text)
            node_text = tree_utils.get_node_text(ch)

            n = Node(node_text, label=[marker], node_type=Node.INTERP)
            node_level = interpretation_level(marker)
        tree_utils.add_to_stack(m_stack, node_level, n)



def process_appendix(m_stack, current_section, child):
    html_parser = HTMLParser.HTMLParser()

    for ch in child.getchildren():
        if ch.tag == 'HD':
            appendix_section = get_appendix_section_number(
                ch.text, current_section)

            if appendix_section is None:
                appendix_section = determine_next_section(m_stack, 2)

            n = Node(
                node_type=Node.APPENDIX, label=[appendix_section],
                title=ch.text)

            node_level = 2
            tree_utils.add_to_stack(m_stack, node_level, n)
        if ch.tag == 'P':
            text = ' '.join([ch.text] + [c.tail for c in ch if c.tail])
            markers_list = tree_utils.get_paragraph_markers(text)

            node_text = tree_utils.get_node_text(ch)

            if len(markers_list) > 0:
                if len(markers_list) > 1:
                    actual_markers = ['(%s)' % m for m in markers_list]
                    node_text = tree_utils.split_text(
                        node_text, actual_markers)
                else:
                    node_text = [node_text]

                for m, node_text in zip(markers_list, node_text):
                    n = Node(
                        node_text, label=[str(m)], node_type=Node.APPENDIX)

                    last = m_stack.peek()
                    node_level = determine_level(m, last[0][0])

                    if m == 'i':
                        #This is bit of a hack, since we can't easily
                        #distinguish between the Roman numeral #(i) and the
                        #letter (i) to determine the level. We look ahead to
                        #help. This is not #a complete solution and we should
                        #circle back at some point.

                        next_text = ' '.join(
                            [ch.getnext().text] +
                            [c.tail for c in ch.getnext() if c.tail])

                        next_markers = tree_utils.get_paragraph_markers(
                            next_text)

                        if next_markers[0] == 'ii':
                            node_level = 5
                    tree_utils.add_to_stack(m_stack, node_level, n)
            else:
                last = m_stack.peek_last()
                last[1].text = last[1].text + '\n %s' % node_text


def appendix_tag(appendix, part):
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
            supps = build_supplement_tree(reg_part, non_reg_sect)
            children.extend(supps)
        else:
            children.append(appendix_tag(non_reg_sect, reg_part))

    return children

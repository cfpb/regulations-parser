#vim: set encoding=utf-8
import string

from lxml import etree
from pyparsing import LineStart, Literal, Optional, Suppress, Word

from regparser.grammar import appendix as grammar
from regparser.grammar.interpretation_headers import parser as headers
from regparser.grammar.utils import Marker
from regparser.tree.node_stack import NodeStack
from regparser.tree.struct import Node
from regparser.tree.xml_parser import tree_utils
from regparser.tree.xml_parser.interpretations import build_supplement_tree
from regparser.tree.xml_parser.interpretations import get_app_title


def process_appendix(appendix, part):
    m_stack = NodeStack()

    counter = 0
    header = 0
    depth = None
    last_hd_level = 0
    appendix_letter = None
    for child in appendix.getchildren():
        # escape clause for interpretations
        if (child.tag == 'HD'
                and 'Supplement I to Part' in tree_utils.get_node_text(child)):
            break
        if ((child.tag == 'HD' and child.attrib['SOURCE'] == 'HED')
                or child.tag == 'RESERVED'):
            appendix_letter = headers.parseString(tree_utils.get_node_text(
                child)).appendix
            n = Node(node_type=Node.APPENDIX, label=[part, appendix_letter],
                     title=tree_utils.get_node_text(child).strip())
            m_stack.push_last((1, n))
            counter = 0
            depth = 2
        elif child.tag == 'HD':
            source = child.attrib.get('SOURCE', 'HD1')
            hd_level = int(source[2:])

            title = tree_utils.get_node_text(child).strip()
            pair = title_label_pair(title, appendix_letter, m_stack)

            #   Use the depth indicated in the title
            if pair:
                label, title_depth = pair
                depth = title_depth + 1
                n = Node(node_type=Node.APPENDIX, label=[label],
                         title=tree_utils.get_node_text(child).strip())
            #   Try to deduce depth from SOURCE attribute
            else:
                header += 1
                n = Node(node_type=Node.APPENDIX, label=['h' + str(header)],
                         title=tree_utils.get_node_text(child).strip())
                if hd_level > last_hd_level:
                    depth += 1
                elif hd_level < last_hd_level:
                    depth = hd_level + 2
                
            last_hd_level = hd_level
            tree_utils.add_to_stack(m_stack, depth - 1, n)
        elif child.tag == 'P' or child.tag == 'FP':
            counter += 1
            text = tree_utils.get_node_text(child)
            n = Node(text, node_type=Node.APPENDIX, label=['p' + str(counter)])
            tree_utils.add_to_stack(m_stack, depth, n)
        elif child.tag == 'GPH':
            counter += 1
            gid = child.xpath('./GID')[0].text
            text = '![](' + gid + ')'
            n = Node(text, node_type=Node.APPENDIX, label=['p' + str(counter)])
            tree_utils.add_to_stack(m_stack, depth, n)

    while m_stack.size() > 1:
        tree_utils.unwind_stack(m_stack)

    if m_stack.m_stack[0]:
        return m_stack.m_stack[0][0][1]


def title_label_pair(text, appendix_letter, stack):
    """Return the label + depth as indicated by a title"""
    digit_str_parser = (LineStart()
                        + Marker(appendix_letter)
                        + Suppress('-')  
                        + grammar.a1
                        + Optional(grammar.paren_upper | grammar.paren_lower))
    for match, _, _ in digit_str_parser.scanString(text):
        #   May need to include the parenthesized letter (if this doesn't
        #   have an appropriate parent)
        if match.paren_upper or match.paren_lower:
            #   Check for a parent with match.a1 as its digit
            parent = stack.peek_level_last(2)
            if parent and parent.label[-1] == match.a1:
                return (match.paren_upper or match.paren_lower, 3)

            return (''.join(match), 2)
        else:
            return (match.a1, 2)


def build_non_reg_text(reg_xml, reg_part):
    """ This builds the tree for the non-regulation text such as Appendices
    and the Supplement section """
    doc_root = etree.fromstring(reg_xml)
    non_reg_sects = doc_root.xpath('//PART//APPENDIX')
    children = []

    for non_reg_sect in non_reg_sects:
        section_title = get_app_title(non_reg_sect)
        if 'Supplement' in section_title and 'Part' in section_title:
            children.append(build_supplement_tree(reg_part, non_reg_sect))
        else:
            children.append(process_appendix(non_reg_sect, reg_part))

    return children

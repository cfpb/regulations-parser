#vim: set encoding=utf-8
from lxml import etree

from regparser.grammar.interpretation_headers import parser as headers
from regparser.tree.node_stack import NodeStack
from regparser.tree.struct import Node
from regparser.tree.xml_parser import tree_utils
from regparser.tree.xml_parser.interpretations import build_supplement_tree
from regparser.tree.xml_parser.interpretations import get_app_title


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

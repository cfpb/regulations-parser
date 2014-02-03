from copy import deepcopy

from regparser.notice.diff import DesignateAmendment
from regparser.notice.util import spaces_then_remove
from regparser.tree.struct import Node, treeify
from regparser.tree.xml_parser import interpretations, tree_utils


def _is_interp_amend(al):
    return (not isinstance(al, DesignateAmendment)
            and Node.INTERP_MARK in al.label)


def parse_interp_changes(amended_labels, cfr_part, parent_xml):
    """Returns an interp structure should it be needed. Tries to build the
    interp tree with the assumption that interpretation headers (e.g.
    "22(b)") are present; if that doesn't work, try matching paragraphs by
    looking at the amended labels"""
    if any(_is_interp_amend(al) for al in amended_labels):
        return (
            process_with_headers(cfr_part, parent_xml)
            or process_without_headers(cfr_part, parent_xml, amended_labels))


def standardize_xml(xml):
    """We will assume a format of Supplement I header followed by HDs,
    STARS, and Ps, so move anything in an EXTRACT up a level"""
    xml = spaces_then_remove(deepcopy(xml), 'PRTPAGE')
    for extract in xml.xpath(".//EXTRACT"):
        ex_parent = extract.getparent()
        idx = ex_parent.index(extract)
        for child in extract:
            ex_parent.insert(idx, child)
            idx += 1
        ex_parent.remove(extract)
    return xml


def process_with_headers(cfr_part, parent_xml):
    """Figure out which parts of the parent_xml are relevant to
    interpretations. Pass those on to interpretations.parse_from_xml and
    return the results"""
    parent_xml = standardize_xml(parent_xml)

    # Skip over everything until 'Supplement I' in a header
    seen_header = False
    xml_nodes = []
    contains_supp = lambda n: 'supplement i' in (n.text.lower() or '')
    for child in parent_xml:
        if seen_header:
            xml_nodes.append(child)
        else:
            if child.tag == 'HD' and contains_supp(child):
                seen_header = True
            for hd in filter(contains_supp, child.xpath(".//HD")):
                seen_header = True

    root = Node(label=[cfr_part, Node.INTERP_MARK], node_type=Node.INTERP)
    root = interpretations.parse_from_xml(root, xml_nodes)
    if not root.children:
        return None
    else:
        return root


def process_without_headers(cfr_part, parent_xml, amended_labels):
    """Sometimes, we only get a list of paragraphs that have changes, but no
    header indicating with which sections they are associated. Accommodate
    by trying to match up amended_labels with paragraphs"""
    parent_xml = standardize_xml(parent_xml)

    relevant_labels = [al.label for al in 
                       filter(_is_interp_amend, amended_labels)]
    label_indices = []
    for idx, child in enumerate(parent_xml):
        text = tree_utils.get_node_text(child)
        if len(relevant_labels) > len(label_indices):
            marker = relevant_labels[len(label_indices)][-1] + '.'
            if text.startswith(marker):
                label_indices.append(idx)

    labelXindex = zip(relevant_labels, label_indices)
    nodes = []
    #   Reverse it so we can delete from the bottom
    for label, idx in reversed(labelXindex):
        stack = tree_utils.NodeStack()
        prefix = label[:label.index(Node.INTERP_MARK) + 1]
        section = Node(node_type=Node.INTERP, label=prefix)
        stack.add(2, section)
        interpretations.process_inner_children(stack, parent_xml[idx - 1])
        while stack.size() > 1:
            stack.unwind()

        nodes.append(stack.m_stack[0][0][1])

        # delete the tail
        while len(parent_xml.getchildren()) > idx:
            parent_xml.remove(parent_xml[idx])
    if nodes:
        nodes.append(Node(node_type=Node.INTERP,
                          label=[cfr_part, Node.INTERP_MARK]))
        #   Reverse it again into normal flow
        return treeify(list(reversed(nodes)))[0]
    else:
        return None

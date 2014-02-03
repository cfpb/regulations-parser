from copy import deepcopy

from regparser.notice.diff import DesignateAmendment
from regparser.notice.util import spaces_then_remove
from regparser.tree.struct import Node
from regparser.tree.xml_parser import interpretations


def parse_interp_changes(amended_labels, cfr_part, parent_xml):
    """Returns an interp structure should it be needed. Tries to build the
    interp tree with the assumption that interpretation headers (e.g.
    "22(b)") are present; if that doesn't work, try matching paragraphs by
    looking at the amended labels"""
    if any(not isinstance(al, DesignateAmendment)
           and Node.INTERP_MARK in al.label for al in amended_labels):
        interp = process_with_headers(cfr_part, parent_xml)
        return interp


def process_with_headers(cfr_part, parent_xml):
    """Figure out which parts of the parent_xml are relevant to
    interpretations. Pass those on to interpretations.parse_from_xml and
    return the results"""
    # First, we try to standardize the xml. We will assume a format of
    # Supplement I header followed by HDs, STARS, and Ps.
    parent_xml = spaces_then_remove(deepcopy(parent_xml), 'PRTPAGE')
    for extract in parent_xml.xpath(".//EXTRACT"):
        ex_parent = extract.getparent()
        idx = ex_parent.index(extract)
        for child in extract:
            ex_parent.insert(idx, child)
            idx += 1
        ex_parent.remove(extract)

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
    return interpretations.parse_from_xml(root, xml_nodes)

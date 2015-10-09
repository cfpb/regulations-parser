# vim: set encoding=utf-8
from copy import deepcopy

from lxml import etree

from regparser.notice.diff import DesignateAmendment
from regparser.notice.util import spaces_then_remove
from regparser.tree.struct import Node
from regparser.tree.xml_parser import interpretations


def _is_interp_amend(al):
    return (not isinstance(al, DesignateAmendment)
            and Node.INTERP_MARK in al.label)


def parse_interp_changes(amended_labels, cfr_part, parent_xml):
    """Returns an interp structure should it be needed. Tries to build the
    interp tree with the assumption that interpretation headers (e.g.
    "22(b)") are present; if that doesn't work, try matching paragraphs by
    looking at the amended labels"""
    if any(_is_interp_amend(al) for al in amended_labels):
        return process_with_headers(cfr_part, parent_xml)


def standardize_xml(xml):
    """We will assume a format of Supplement I header followed by HDs,
    STARS, and Ps, so move anything in an EXTRACT up a level"""
    xml = spaces_then_remove(deepcopy(xml), 'PRTPAGE')
    for extract in xml.xpath(".//EXTRACT|.//APPENDIX|.//SUBPART"):
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
    root_title = None
    xml_nodes = []
    contains_supp = lambda n: 'supplement i' in (n.text.lower() or '')
    for child in parent_xml:
        # SECTION shouldn't be in this part of the XML, but often is. Expand
        # it to proceed
        if seen_header and child.tag == 'SECTION':
            sectno = child.xpath('./SECTNO')[0]
            subject = child.xpath('./SUBJECT')[0]
            header = etree.Element("HD", SOURCE="HD2")
            header.text = sectno.text + u'—' + subject.text
            child.insert(child.index(sectno), header)
            child.remove(sectno)
            child.remove(subject)
            xml_nodes.extend(child.getchildren())
        elif seen_header:
            xml_nodes.append(child)
        else:
            if child.tag == 'HD' and contains_supp(child):
                root_title = child.text
                seen_header = True
            for hd in filter(contains_supp, child.xpath(".//HD")):
                seen_header = True

    if root_title:
        root = Node(label=[cfr_part, Node.INTERP_MARK], node_type=Node.INTERP,
                    title=root_title)
    else:
        root = Node(label=[cfr_part, Node.INTERP_MARK], node_type=Node.INTERP)
    root = interpretations.parse_from_xml(root, xml_nodes)
    if not root.children:
        return None
    else:
        return root

# vim: set encoding=utf-8
import logging
from itertools import takewhile
import re

from lxml import etree
from pyparsing import LineStart, Optional, Suppress

from regparser.citations import internal_citations
from regparser.grammar import appendix as grammar
from regparser.grammar.interpretation_headers import parser as headers
from regparser.grammar.utils import Marker
from regparser.layer.formatting import table_xml_to_plaintext
from regparser.layer.key_terms import KeyTerms
from regparser.tree.depth import markers
from regparser.tree.depth.derive import derive_depths
from regparser.tree.paragraph import p_levels
from regparser.tree.struct import Node
from regparser.tree.xml_parser import tree_utils
from regparser.tree.xml_parser.interpretations import build_supplement_tree
from regparser.tree.xml_parser.interpretations import get_app_title

from settings import APPENDIX_IGNORE_SUBHEADER_LABEL


def remove_toc(appendix, letter):
    """The TOC at the top of certain appendices gives us trouble since it
    looks a *lot* like a sequence of headers. Remove it if present"""
    fingerprints = set()
    potential_toc = set()
    for node in appendix.xpath("./HD[@SOURCE='HED']/following-sibling::*"):
        parsed = parsed_title(tree_utils.get_node_text(node), letter)
        if parsed:
            #  The headers may not match character-per-character. Only
            #  compare the parsed results.
            fingerprint = tuple(parsed)
            #  Hit the real content

            if fingerprint in fingerprints and node.tag == 'HD':
                for el in potential_toc:
                    el.getparent().remove(el)
                return
            else:
                fingerprints.add(fingerprint)
                potential_toc.add(node)
        elif node.tag != 'GPH':     # Not a title and not a img => no TOC
            return


def is_appendix_header(node):
    return (node.tag == 'RESERVED'
            or (node.tag == 'HD' and node.attrib['SOURCE'] == 'HED'))


class AppendixProcessor(object):
    """Processing the appendix requires a lot of state to be carried in
    between xml nodes. Use a class to wrap that state so we can
    compartmentalize processing the various tags"""

    #   Placeholder text/headers have the label p1 or h1; use that as an
    #   identifier when determining which depth elements should be placed
    filler_regex = re.compile(r"[ph]\d+")

    def set_letter(self, appendix):
        """Find (and set) the appendix letter"""
        for node in (c for c in appendix.getchildren()
                     if is_appendix_header(c)):
            text = tree_utils.get_node_text(node)
            if self.appendix_letter:
                logging.warning("Found two appendix headers: %s and %s",
                                self.appendix_letter, text)
            parsed_header = headers.parseString(text)
            self.appendix_letter = parsed_header.appendix

        return self.appendix_letter

    def hed(self, part, text):
        """HD with an HED source indicates the root of the appendix"""
        n = Node(node_type=Node.APPENDIX, label=[part, self.appendix_letter],
                 title=text)
        self.m_stack.push_last((0, n))
        self.paragraph_counter = 0
        self.depth = 0

    def depth_from_ancestry(self, source_attr):
        """Subheaders without explicit depth markers (e.g. Part I) are
        tricky. We look through their parents, trying to find a previous
        header that shared its SOURCE level (the next node would also share
        node level). If that doesn't work, find the last header and set
        depth on higher (as the next node is an unseen level)."""

        def not_known_depth_header(pair):
            """Hitting a know-depth header (see above) means we've gone too
            far"""
            lvl, parent = pair
            return (not parent.title
                    or not title_label_pair(parent.title,
                                            self.appendix_letter, self.part))

        #   Check if this SOURCE level matches a previous
        for lvl, parent in takewhile(not_known_depth_header,
                                     self.m_stack.lineage_with_level()):
            if (parent.source_xml is not None
                    and parent.source_xml.attrib.get('SOURCE') == source_attr):
                return lvl

        #   Second pass, search for any header; place self one lower
        for lvl, parent in self.m_stack.lineage_with_level():
            if parent.title:
                pair = title_label_pair(parent.title,
                                        self.appendix_letter, self.part)
                if pair:
                    return pair[1]
                else:
                    return lvl + 1
            if not AppendixProcessor.filler_regex.match(parent.label[-1]):
                return lvl + 1

    def subheader(self, xml_node, text):
        """Each appendix may contain multiple subheaders. Some of these are
        obviously labeled (e.g. A-3 or Part III) and others are headers
        without a specific label (we give them the h + # id)"""
        source = xml_node.attrib.get('SOURCE')

        pair = title_label_pair(text, self.appendix_letter, self.part)

        #   Use the depth indicated in the title
        if pair:
            label, title_depth = pair
            self.depth = title_depth - 1
            n = Node(node_type=Node.APPENDIX, label=[label],
                     title=text, source_xml=xml_node)
        #   Look through parents to determine which level this should be
        else:
            self.header_count += 1

            n = Node(node_type=Node.APPENDIX, title=text,
                     label=['h' + str(self.header_count)],
                     source_xml=xml_node)
            self.depth = self.depth_from_ancestry(source)

        self.m_stack.add(self.depth, n)

    def insert_dashes(self, xml_node, text):
        """ If paragraph has a SOURCE attribute with a value of FP-DASH
            it fills out with dashes, like Foo_____. """
        mtext = text
        if xml_node.get('SOURCE') == 'FP-DASH':
            mtext = mtext + '_____'
        return mtext

    def process_sequence(self, root):
        for child in root.getchildren():
            text = tree_utils.get_node_text(child, add_spaces=True).strip()
            text = self.insert_dashes(child, text)
            self.paragraph_with_marker(
                text, tree_utils.get_node_text_tags_preserved(child))

        old_depth = self.depth
        self.depth += 1
        self.end_group()
        self.depth = old_depth

    def paragraph_with_marker(self, text, tagged_text):
        """The paragraph has a marker, like (a) or a. etc."""
        # To aid in determining collapsed paragraphs, replace any
        # keyterms present
        node_for_keyterms = Node(text, node_type=Node.APPENDIX)
        node_for_keyterms.tagged_text = tagged_text
        node_for_keyterms.label = [initial_marker(text)[0]]
        keyterm = KeyTerms.get_keyterm(node_for_keyterms)
        if keyterm:
            mtext = text.replace(keyterm, ';'*len(keyterm))
        else:
            mtext = text

        for mtext in split_paragraph_text(mtext):
            if keyterm:     # still need the original text
                mtext = mtext.replace(';'*len(keyterm), keyterm)
            # label_candidate = [initial_marker(mtext)[0]]
            # existing_node = None
            # for node in self.nodes:
            #     if node.label == label_candidate:
            #         existing_node = node
            # if existing_node:
            #     self.paragraph_counter += 1
            #     node = Node(mtext, node_type=Node.APPENDIX,
            #                 label=['dup{}'.format(self.paragraph_counter),
            #                        initial_marker(mtext)[0]])
            # else:
            node = Node(mtext, node_type=Node.APPENDIX,
                        label=[initial_marker(mtext)[0]])
            node.tagged_text = tagged_text
            self.nodes.append(node)

    def paragraph_no_marker(self, text):
        """The paragraph has no (a) or a. etc."""
        self.paragraph_counter += 1
        n = Node(text, node_type=Node.APPENDIX,
                 label=['p' + str(self.paragraph_counter)])
        self.nodes.append(n)

    def graphic(self, xml_node):
        self.paragraph_counter += 1
        gid = xml_node.xpath('./GID')[0].text
        text = '![](' + gid + ')'
        n = Node(text, node_type=Node.APPENDIX,
                 label=['p' + str(self.paragraph_counter)])
        self.nodes.append(n)

    def table(self, xml_node):
        self.paragraph_counter += 1
        n = Node(table_xml_to_plaintext(xml_node),
                 node_type=Node.APPENDIX,
                 label=['p' + str(self.paragraph_counter)],
                 source_xml=xml_node)
        self.nodes.append(n)

    def fence(self, xml_node, fence_type):
        """Use github-like fencing to indicate this is a note or code"""
        self.paragraph_counter += 1
        texts = ["```" + fence_type]
        for child in xml_node:
            texts.append(tree_utils.get_node_text(child).strip())
        texts.append("```")
        n = Node("\n".join(texts), node_type=Node.APPENDIX,
                 label=['p' + str(self.paragraph_counter)],
                 source_xml=xml_node)
        self.nodes.append(n)

    def depth_zero_finder(self, node):
        """Look back through all known nodes to see if this is a
        continuation of a previous set of paragraph markers"""
        for depth, prev_node in self.m_stack.lineage_with_level():
            for typ in (markers.lower, markers.upper, markers.ints,
                        markers.roman):
                if prev_node.label[-1] in typ and node.label[-1] in typ:
                    typ = list(typ)
                    prev_idx = typ.index(prev_node.label[-1])
                    current_idx = typ.index(node.label[-1])
                    if current_idx == prev_idx + 1:
                        return depth
        # Paragraphs under the main heading should not be level 2
        if len(self.m_stack.lineage()) == 1:
            return self.depth
        else:
            return self.depth + 1

    def end_group(self):
        """We've hit a header (or the end of the appendix), so take the
        collected paragraphs and determine their depths and insert into the
        heap accordingly"""
        if self.nodes:
            nodes = list(reversed(self.nodes))
            markers = [n.label[-1] for n in self.nodes if not
                       AppendixProcessor.filler_regex.match(n.label[-1])]
            if markers:
                results = derive_depths(markers)
                if not results or results == []:
                    logging.warning(
                        'Could not derive depth from {}'.format(markers))
                    depths = []
                else:
                    depths = list(reversed(
                        [a.depth for a in results[0].assignment]))
            else:
                depths = []
            depth_zero = None   # relative for beginning of marker depth
            self.depth += 1
            while nodes:
                node = nodes.pop()
                if (AppendixProcessor.filler_regex.match(node.label[-1])
                        or depths == []):
                    # Not a marker paragraph, or a marker paragraph that isn't
                    # actually part of a hierarchy (e.g. Appendix C to 1024,
                    # notice 2013-28210)
                    self.m_stack.add(self.depth, node)
                else:
                    depth = depths.pop()
                    # Match old behavior, placing marker paragraphs as
                    # children within non-marker paragraphs above
                    if depth_zero is None:
                        depth_zero = self.depth_zero_finder(node)
                    self.depth = depth_zero + depth
                    self.m_stack.add(self.depth, node)
            self.nodes = []

    def process(self, appendix, part):
        self.m_stack = tree_utils.NodeStack()

        self.part = part
        self.paragraph_count = 0
        self.header_count = 0
        self.depth = None
        self.appendix_letter = None
        # holds collections of nodes until their depth is determined
        self.nodes = []

        self.set_letter(appendix)
        remove_toc(appendix, self.appendix_letter)

        def is_subhead(tag, text):
            initial = initial_marker(text)
            return ((tag == 'HD' and (not initial or '.' in initial[1]))
                    or (tag in ('P', 'FP')
                        and title_label_pair(text, self.appendix_letter,
                                             self.part)))

        for child in appendix.getchildren():
            text = tree_utils.get_node_text(child, add_spaces=True).strip()
            if ((child.tag == 'HD' and child.attrib['SOURCE'] == 'HED')
                    or child.tag == 'RESERVED'):
                self.end_group()
                self.hed(part, text)
            elif is_subhead(child.tag, text):
                self.end_group()
                self.subheader(child, text)
            elif initial_marker(text) and child.tag in ('P', 'FP', 'HD'):
                text = self.insert_dashes(child, text)
                self.paragraph_with_marker(
                    text,
                    tree_utils.get_node_text_tags_preserved(child))
            elif child.tag == 'SEQUENCE':
                old_depth = self.depth
                self.end_group()
                self.depth = old_depth
                self.process_sequence(child)
            elif child.tag in ('P', 'FP'):
                text = self.insert_dashes(child, text)
                self.paragraph_no_marker(text)
            elif child.tag == 'GPH':
                self.graphic(child)
            elif child.tag == 'GPOTABLE':
                self.table(child)
            elif child.tag in ('NOTE', 'NOTES'):
                self.fence(child, 'note')
            elif child.tag == 'CODE':
                self.fence(child, child.get('LANGUAGE', 'code'))

        self.end_group()
        while self.m_stack.size() > 1:
            self.m_stack.unwind()

        if self.m_stack.m_stack[0]:
            return self.m_stack.m_stack[0][0][1]


_first_paren_markers = [re.compile(ur'[\)\.|,|;|-|—]\s*(\(' + lvl[0] + '\))')
                        for lvl in p_levels]
_first_period_markers = [re.compile(ur'[\)\.|,|;|-|—]\s*(' + lvl[0] + '\.)')

                         for lvl in p_levels]


def split_paragraph_text(text):
    """Split text into a root node and its children (if the text contains
    collapsed markers"""
    marker_positions = []
    if text.lstrip()[:1] == '(':
        marker_set = _first_paren_markers
    else:
        marker_set = _first_period_markers
    for marker in marker_set:
        marker_positions.extend(m.end() - len(m.group(1))
                                for m in marker.finditer(text))
    #   Remove any citations
    citations = internal_citations(text, require_marker=True)
    marker_positions = [pos for pos in marker_positions
                        if not any(cit.start <= pos and cit.end >= pos
                                   for cit in citations)]
    texts = []
    #   Drop Zeros, add the end
    break_points = [p for p in marker_positions if p] + [len(text)]
    last_pos = 0
    for pos in break_points:
        texts.append(text[last_pos:pos])
        last_pos = pos
    return texts


def process_appendix(appendix, part):
    return AppendixProcessor().process(appendix, part)


def parsed_title(text, appendix_letter):
    digit_str_parser = (Optional(Suppress("Appendix"))
                        + Marker(appendix_letter)
                        + Suppress('-')
                        + grammar.a1.copy().leaveWhitespace()
                        + Optional(grammar.markerless_upper)
                        + Optional(grammar.paren_upper | grammar.paren_lower)
                        + Optional(grammar.paren_digit))
    part_roman_parser = Marker("part") + grammar.aI
    parser = LineStart() + (digit_str_parser
                            | part_roman_parser
                            | grammar.roman_upper)

    for match, _, _ in parser.scanString(text):
        return match


def title_label_pair(text, appendix_letter, reg_part):
    """Return the label + depth as indicated by a title"""
    pair = None
    match = parsed_title(text, appendix_letter)
    if match:
        #   May need to include the parenthesized letter(s)
        has_parens = (match.paren_upper or match.paren_lower
                      or match.paren_digit or match.markerless_upper)
        if has_parens:
            pair = (''.join(match), 2)
        elif match.a1:
            pair = (match.a1, 2)
        elif match.aI:
            pair = (match.aI, 2)
        elif match.roman_upper and reg_part in text:
            pair = (match.roman_upper, 2)

        if pair is not None and \
                reg_part in APPENDIX_IGNORE_SUBHEADER_LABEL and \
                pair[0] in APPENDIX_IGNORE_SUBHEADER_LABEL[reg_part][
                    appendix_letter]:
            logging.warning("Ignoring subheader label %s of appendix %s",
                            pair[0], appendix_letter)
            pair = None

    return pair


def initial_marker(text):
    parser = (grammar.paren_upper | grammar.paren_lower | grammar.paren_digit
              | grammar.period_upper | grammar.period_digit
              | grammar.period_lower | grammar.roman_upper)
    for match, start, end in parser.scanString(text):
        if start != 0:
            continue
        marker = (match.paren_upper or match.paren_lower or match.paren_digit
                  or match.period_upper or match.period_lower
                  or match.period_digit)

        if len(marker) < 3 or all(char in 'ivxlcdm' for char in marker):
            return marker, text[:end]


def build_non_reg_text(reg_xml, reg_part):
    """ This builds the tree for the non-regulation text such as Appendices
    and the Supplement section """
    if isinstance(reg_xml, str) or isinstance(reg_xml, unicode):
        doc_root = etree.fromstring(reg_xml)
    else:
        doc_root = reg_xml
    non_reg_sects = doc_root.xpath('//PART//APPENDIX')
    children = []

    for non_reg_sect in non_reg_sects:
        section_title = get_app_title(non_reg_sect)
        if 'Supplement' in section_title and 'Part' in section_title:
            children.append(build_supplement_tree(reg_part, non_reg_sect))
        else:
            children.append(process_appendix(non_reg_sect, reg_part))

    return children

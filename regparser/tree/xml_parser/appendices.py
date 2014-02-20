#vim: set encoding=utf-8
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
from regparser.tree.paragraph import p_levels
from regparser.tree.struct import Node, walk
from regparser.tree.xml_parser import tree_utils
from regparser.tree.xml_parser.interpretations import build_supplement_tree
from regparser.tree.xml_parser.interpretations import get_app_title


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


_first_markers = [re.compile(ur'[\)\.|,|;|-|—]\s*\(' + lvl[0] + '\)')
                  for lvl in p_levels]


def in_same_p_level(node, stack_level):
    """Given a node and a stack level (i.e. a list of (depth, node) pairs),
    check if the node should be in the same paragraph depth as the stack
    level. Do this by checking what types of labels are present in the stack
    level."""
    stack_level = filter(lambda pr: hasattr(pr[1], 'p_level'), stack_level)
    if not hasattr(node, 'p_level'):
        return len(stack_level) == 0
    else:
        if stack_level:
            prev_node = stack_level[-1][1]
            prev_level = prev_node.p_level
        else:
            prev_node, prev_level = None, None
        par_level = p_levels[node.p_level]
        return (prev_level == node.p_level and
                par_level.index(prev_node.label[-1]) <
                par_level.index(node.label[-1]))


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
            self.appendix_letter = headers.parseString(text).appendix
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
                                            self.appendix_letter))

        #   Check if this SOURCE level matches a previous
        for lvl, parent in takewhile(not_known_depth_header,
                                     self.m_stack.lineage_with_level()):
            if (parent.source_xml is not None
                    and parent.source_xml.attrib.get('SOURCE') == source_attr):
                return lvl

        #   Second pass, search for any header; place self one lower
        for lvl, parent in self.m_stack.lineage_with_level():
            if parent.title:
                pair = title_label_pair(parent.title, self.appendix_letter)
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

        pair = title_label_pair(text, self.appendix_letter)

        #   Use the depth indicated in the title
        if pair:
            label, title_depth = pair
            self.depth = title_depth - 1
            n = Node(node_type=Node.APPENDIX, label=[label],
                     title=text)
        #   Look through parents to determine which level this should be
        else:
            self.header_count += 1
            n = Node(node_type=Node.APPENDIX, title=text,
                     label=['h' + str(self.header_count)],
                     source_xml=xml_node)
            self.depth = self.depth_from_ancestry(source)

        self.m_stack.add(self.depth, n)

    def _indent_if_needed(self):
        """Indents one level if preceded by a header"""
        last = self.m_stack.peek()
        if last and last[-1][1].title:
            self.depth += 1

    def paragraph_no_marker(self, text):
        """The paragraph has no (a) or a. etc. Indents one level if
        preceded by a header"""
        self.paragraph_counter += 1
        n = Node(text, node_type=Node.APPENDIX,
                 label=['p' + str(self.paragraph_counter)])

        self._indent_if_needed()
        self.m_stack.add(self.depth, n)

    def find_next_text_with_marker(self, node):
        """Scan xml nodes and their neighbors looking for text that begins
        with a marker. When found, return it"""
        if node.tag == 'HD':   # Next section; give up
            return None
        if node.tag in ('P', 'FP'):     # Potential text
            text = tree_utils.get_node_text(node)
            pair = initial_marker(text)
            if pair:
                return text
        if node.getnext() is None:  # end of the line
            return None
        return self.find_next_text_with_marker(node.getnext())

    def split_paragraph_text(self, text, next_text=''):
        marker_positions = []
        for marker in _first_markers:
            #   text.index('(') to skip over the periods, spaces, etc.
            marker_positions.extend(text.index('(', m.start())
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
        texts.append(next_text)
        return texts

    def paragraph_with_marker(self, text, next_text=''):
        """The paragraph has an (a) or a. etc."""
        marker, _ = initial_marker(text)
        n = Node(text, node_type=Node.APPENDIX, label=[marker])

        if initial_marker(next_text):
            next_marker, _ = initial_marker(next_text)
        else:
            next_marker = None

        this_p_levels = set(idx for idx, lvl in enumerate(p_levels)
                            if marker in lvl)
        next_p_levels = set(idx for idx, lvl in enumerate(p_levels)
                            if next_marker in lvl)
        previous_levels = [l for l in self.m_stack.m_stack if l]
        previous_p_levels = set()
        for stack_level in previous_levels:
            previous_p_levels.update(sn.p_level for _, sn in stack_level
                                     if hasattr(sn, 'p_level'))

        #   Ambiguity, e.g. 'i', 'v'. Disambiguate by looking forward
        if len(this_p_levels) > 1 and len(next_p_levels) == 1:
            next_p_level = next_p_levels.pop()
            #   e.g. an 'i' followed by a 'ii'
            if next_p_level in this_p_levels:
                this_p_idx = p_levels[next_p_level].index(marker)
                next_p_idx = p_levels[next_p_level].index(next_marker)
                if this_p_idx < next_p_idx:     # Heuristic
                    n.p_level = next_p_level
            #   e.g. (a)(1)(i) followed by an 'A'
            new_level = this_p_levels - previous_p_levels
            if next_p_level not in previous_p_levels and new_level:
                n.p_level = new_level.pop()

        #   Ambiguity. Disambiguate by looking backwards
        if len(this_p_levels) > 1 and not hasattr(n, 'p_level'):
            for stack_level in previous_levels:
                for lvl, stack_node in stack_level:
                    if getattr(stack_node, 'p_level', None) in this_p_levels:
                        #   Later levels replace earlier ones
                        n.p_level = stack_node.p_level

        #   Simple case (no ambiguity) and cases not seen above
        if not getattr(n, 'p_level', None):
            n.p_level = min(this_p_levels)  # rule of thumb: favor lower case

        #   Check if we've seen this type of marker before
        found_in_prev = False
        for stack_level in previous_levels:
            if stack_level and in_same_p_level(n, stack_level):
                found_in_prev = True
                self.depth = stack_level[-1][0]
        if not found_in_prev:   # New type of marker
            self.depth += 1
        self.m_stack.add(self.depth, n)

    def graphic(self, xml_node):
        """An image. Indents one level if preceded by a header"""
        self.paragraph_counter += 1
        gid = xml_node.xpath('./GID')[0].text
        text = '![](' + gid + ')'
        n = Node(text, node_type=Node.APPENDIX,
                 label=['p' + str(self.paragraph_counter)])

        self._indent_if_needed()
        self.m_stack.add(self.depth, n)

    def table(self, xml_node):
        """A table. Indents one level if preceded by a header"""
        self.paragraph_counter += 1
        n = Node(table_xml_to_plaintext(xml_node),
                 node_type=Node.APPENDIX,
                 label=['p' + str(self.paragraph_counter)],
                 source_xml=xml_node)

        self._indent_if_needed()
        self.m_stack.add(self.depth, n)

    def note(self, xml_node):
        """Use github-like fencing to indicate this is a note"""
        self.paragraph_counter += 1
        texts = ["```note"]
        for child in xml_node:
            texts.append(tree_utils.get_node_text(child).strip())
        texts.append("```")
        n = Node("\n".join(texts), node_type=Node.APPENDIX,
                 label=['p' + str(self.paragraph_counter)],
                 source_xml=xml_node)

        self._indent_if_needed()
        self.m_stack.add(self.depth, n)

    def process(self, appendix, part):
        self.m_stack = tree_utils.NodeStack()

        self.paragraph_count = 0
        self.header_count = 0
        self.depth = None
        self.appendix_letter = None

        self.set_letter(appendix)
        remove_toc(appendix, self.appendix_letter)

        def is_subhead(tag, text):
            initial = initial_marker(text)
            return ((tag == 'HD' and (not initial or '.' in initial[1]))
                    or (tag in ('P', 'FP')
                        and title_label_pair(text, self.appendix_letter)))

        for child in appendix.getchildren():
            text = tree_utils.get_node_text(child).strip()
            if ((child.tag == 'HD' and child.attrib['SOURCE'] == 'HED')
                    or child.tag == 'RESERVED'):
                self.hed(part, text)
            elif is_subhead(child.tag, text):
                self.subheader(child, text)
            elif initial_marker(text) and child.tag in ('P', 'FP', 'HD'):
                if child.getnext() is None:
                    next_text = ''
                else:
                    next_text = self.find_next_text_with_marker(
                        child.getnext()) or ''
                texts = self.split_paragraph_text(text, next_text)
                for text, next_text in zip(texts, texts[1:]):
                    self.paragraph_with_marker(text, next_text)
            elif child.tag in ('P', 'FP'):
                self.paragraph_no_marker(text)
            elif child.tag == 'GPH':
                self.graphic(child)
            elif child.tag == 'GPOTABLE':
                self.table(child)
            elif child.tag in ('NOTE', 'NOTES'):
                self.note(child)

        while self.m_stack.size() > 1:
            self.m_stack.unwind()

        if self.m_stack.m_stack[0]:
            root = self.m_stack.m_stack[0][0][1]

            def per_node(n):
                if hasattr(n, 'p_level'):
                    del n.p_level

            walk(root, per_node)
            return root


def process_appendix(appendix, part):
    return AppendixProcessor().process(appendix, part)


def parsed_title(text, appendix_letter):
    digit_str_parser = (Marker(appendix_letter)
                        + Suppress('-')
                        + grammar.a1.copy().leaveWhitespace()
                        + Optional(grammar.markerless_upper)
                        + Optional(grammar.paren_upper | grammar.paren_lower)
                        + Optional(grammar.paren_digit))
    part_roman_parser = Marker("part") + grammar.aI
    parser = LineStart() + (digit_str_parser | part_roman_parser)

    for match, _, _ in parser.scanString(text):
        return match


def title_label_pair(text, appendix_letter):
    """Return the label + depth as indicated by a title"""
    match = parsed_title(text, appendix_letter)
    if match:
        #   May need to include the parenthesized letter(s)
        has_parens = (match.paren_upper or match.paren_lower
                      or match.paren_digit or match.markerless_upper)
        if has_parens:
            return (''.join(match), 2)
        elif match.a1:
            return (match.a1, 2)
        elif match.aI:
            return (match.aI, 2)


def initial_marker(text):
    parser = (grammar.paren_upper | grammar.paren_lower | grammar.paren_digit
              | grammar.period_upper | grammar.period_digit
              | grammar.period_lower)
    for match, start, end in parser.scanString(text):
        if start != 0:
            continue
        marker = (match.paren_upper or match.paren_lower or match.paren_digit
                  or match.period_upper or match.period_lower
                  or match.period_digit)
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

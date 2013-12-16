#vim: set encoding=utf-8
import re
import string

from lxml import etree
from pyparsing import LineStart, Literal, Optional, Suppress, Word

from regparser.grammar import appendix as grammar
from regparser.grammar.interpretation_headers import parser as headers
from regparser.grammar.utils import Marker
from regparser.tree.node_stack import NodeStack
from regparser.tree.paragraph import p_levels
from regparser.tree.struct import Node
from regparser.tree.xml_parser import tree_utils
from regparser.tree.xml_parser.interpretations import build_supplement_tree
from regparser.tree.xml_parser.interpretations import get_app_title


def remove_toc(appendix, letter):
    """The TOC at the top of certain appendices gives us trouble since it
    looks a *lot* like a sequence of headers. Remove it if present"""
    headers = set()
    potential_toc = set()
    for node in appendix.xpath("./HD[@SOURCE='HED']/following-sibling::*"):
        parsed = parsed_title(tree_utils.get_node_text(node), letter)
        if parsed:
            #  The headers may not match character-per-character. Only
            #  compare the parsed results.
            fingerprint = tuple(parsed)
            #  Hit the real content
            if fingerprint in headers and node.tag == 'HD':
                for el in potential_toc:
                    el.getparent().remove(el)
                return
            else:
                headers.add(fingerprint)
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

    def subheader(self, xml_node, text):
        """Each appendix may contain multiple subheaders. Some of these are
        obviously labeled (e.g. A-3 or Part III) and others are headers
        without a specific label (we give them the h + # id)"""
        source = xml_node.attrib.get('SOURCE', 'HD1')
        hd_level = int(source[2:])

        pair = title_label_pair(text, self.appendix_letter, self.m_stack)

        #   Use the depth indicated in the title
        if pair:
            label, title_depth = pair
            self.depth = title_depth - 1
            n = Node(node_type=Node.APPENDIX, label=[label],
                     title=text)
        #   Try to deduce depth from SOURCE attribute
        else:
            self.header_count += 1
            n = Node(node_type=Node.APPENDIX, title=text,
                     label=['h' + str(self.header_count)])
            self.depth = hd_level

        tree_utils.add_to_stack(self.m_stack, self.depth, n)

    def paragraph_no_marker(self, text):
        """The paragraph has no (a) or a. etc. Indents one level if
        preceded by a header"""
        self.paragraph_counter += 1
        n = Node(text, node_type=Node.APPENDIX,
                 label=['p' + str(self.paragraph_counter)])
        n.irregular = True

        last = self.m_stack.peek()
        if last and last[-1][1].title:
            self.depth += 1
        tree_utils.add_to_stack(self.m_stack, self.depth, n)

    def paragraph_with_marker(self, text):
        """The paragraph has an (a) or a. etc."""
        marker, _ = initial_marker(text)
        n = Node(text, node_type=Node.APPENDIX, label=[marker])
        this_levels = set(idx for idx, lvl in enumerate(p_levels)
                          if marker in lvl)

        stack_levels = [l for l in self.m_stack.m_stack if l]
        is_previous_level = False
        for level in stack_levels:
            #   We only care about nodes that are well defined (i.e. have a
            #   proper label)
            level = [pair for pair in level
                     if not getattr(pair[1], 'irregular', False)]
            if not level:
                continue
            depth, last_node = level[-1]
            last_marker = last_node.label[-1]
            last_levels = set(idx for idx, lvl in enumerate(p_levels)
                              if last_marker in lvl)
            if (this_levels & last_levels and not last_node.title
                and not is_previous_level):
                    self.depth = depth
                    is_previous_level = True

        if not is_previous_level:
            self.depth += 1
        tree_utils.add_to_stack(self.m_stack, self.depth, n)

    def graphic(self, xml_node):
        """An image. Indents one level if preceded by a header"""
        self.paragraph_counter += 1
        gid = xml_node.xpath('./GID')[0].text
        text = '![](' + gid + ')'
        n = Node(text, node_type=Node.APPENDIX,
                 label=['p' + str(self.paragraph_counter)])

        last = self.m_stack.peek()
        if last and last[-1][1].title:
            self.depth += 1
        tree_utils.add_to_stack(self.m_stack, self.depth, n)

    def process(self, appendix, part):
        self.m_stack = NodeStack()

        self.paragraph_count = 0
        self.header_count = 0
        self.depth = None
        self.appendix_letter = None

        self.set_letter(appendix)
        remove_toc(appendix, self.appendix_letter)

        for child in appendix.getchildren():
            text = tree_utils.get_node_text(child).strip()
            if ((child.tag == 'HD' and child.attrib['SOURCE'] == 'HED')
                    or child.tag == 'RESERVED'):
                self.hed(part, text)
            elif (child.tag == 'HD'
                  or (child.tag in ('P', 'FP')
                      and title_label_pair(text, self.appendix_letter,
                                           self.m_stack))):
                self.subheader(child, text)
            elif initial_marker(text) and child.tag in ('P', 'FP'):
                self.paragraph_with_marker(text)
            elif child.tag in ('P', 'FP'):
                self.paragraph_no_marker(text)
            elif child.tag == 'GPH':
                self.graphic(child)

        while self.m_stack.size() > 1:
            tree_utils.unwind_stack(self.m_stack)

        if self.m_stack.m_stack[0]:
            return self.m_stack.m_stack[0][0][1]


def process_appendix(appendix, part):
    return AppendixProcessor().process(appendix, part)


def parsed_title(text, appendix_letter):
    digit_str_parser = (Marker(appendix_letter)
                        + Suppress('-')
                        + grammar.a1
                        + Optional(grammar.paren_upper | grammar.paren_lower))
    part_roman_parser = Marker("part") + grammar.aI
    parser = LineStart() + (digit_str_parser | part_roman_parser)

    for match, _, _ in parser.scanString(text):
        return match


def title_label_pair(text, appendix_letter, stack=None):
    """Return the label + depth as indicated by a title"""
    match = parsed_title(text, appendix_letter)
    if match:
        #   May need to include the parenthesized letter (if this doesn't
        #   have an appropriate parent)
        if stack and (match.paren_upper or match.paren_lower):
            #   Check for a parent with match.a1 as its digit
            parent = stack.peek_level_last(2)
            if parent and parent.label[-1] == match.a1:
                return (match.paren_upper or match.paren_lower, 3)

            return (''.join(match), 2)
        elif match.a1:
            return (match.a1, 2)
        elif match.aI:
            return (match.aI, 2)


def initial_marker(text):
    parser = (grammar.paren_upper | grammar.paren_lower | grammar.paren_digit
              | grammar.period_upper | grammar.period_digit )
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

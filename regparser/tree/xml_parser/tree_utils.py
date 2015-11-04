# vim: set encoding=utf-8
from copy import deepcopy
import HTMLParser
from itertools import chain

from pyparsing import Literal, Optional, Regex, Suppress

from regparser.citations import remove_citation_overlaps
from regparser.tree.depth import markers as mtypes
from regparser.tree.paragraph import p_levels
from regparser.tree.priority_stack import PriorityStack


def prepend_parts(parts_prefix, n):
    """ Recursively preprend parts_prefix to the parts of the node
    n. Parts is a list of markers that indicates where you are in the
    regulation text. """

    n.label = parts_prefix + n.label

    for c in n.children:
        prepend_parts(parts_prefix, c)
    return n


class NodeStack(PriorityStack):
    """ The NodeStack aids our construction of a struct.Node tree. We process
    xml one paragraph at a time; using a priority stack allows us to insert
    items at their proper depth and unwind the stack (collecting children) as
    necessary"""
    def unwind(self):
        """ Unwind the stack, collapsing sub-paragraphs that are on the stack
        into the children of the previous level. """
        children = self.pop()
        parts_prefix = self.peek_last()[1].label
        children = [prepend_parts(parts_prefix, c[1]) for c in children]
        self.peek_last()[1].children = children


def split_text(text, tokens):
    """
        Given a body of text that contains tokens,
        splice the text along those tokens.
    """
    starts = [text.find(t) for t in tokens]
    slices = zip(starts, starts[1:])
    texts = [text[i[0]:i[1]] for i in slices] + [text[starts[-1]:]]
    return texts


_first_markers = []
for idx, level in enumerate(p_levels):
    marker = (Suppress(Regex(u',|\.|-|—|>'))
              + Suppress('(')
              + Literal(level[0])
              + Suppress(')'))
    for inner_idx in range(idx + 1, len(p_levels)):
        inner_level = p_levels[inner_idx]
        marker += Optional(Suppress('(')
                           + Literal(inner_level[0])
                           + Suppress(')'))
    _first_markers.append(marker)


# @profile
def get_collapsed_markers(text):
    """Not all paragraph markers are at the beginning of of the text. This
    grabs inner markers like (1) and (i) here:
    (c) cContent —(1) 1Content (i) iContent"""

    matches = []
    for parser in _first_markers:
        matches.extend(parser.scanString(text))

    #   remove matches at the beginning
    if matches and matches[0][1] == 0:
        matches = matches[1:]

    #   remove any that overlap with citations
    matches = [m for m, _, _ in remove_citation_overlaps(text, matches)]

    #   get the letters; poor man's flatten
    return reduce(lambda lhs, rhs: list(lhs) + list(rhs), matches, [])


def get_paragraph_markers(text):
    """ From a body of text that contains paragraph markers, extract the
    initial markers. """

    markers = []
    text = text.lstrip()
    for mtype in (mtypes.lower, mtypes.ints, mtypes.roman, mtypes.upper,
                  mtypes.em_ints, mtypes.em_roman):
        for marker in mtype:
            if text.startswith('(' + marker + ')'):
                markers.append(marker)
                text = text[2 + len(marker):].lstrip()
                break
    return markers


def _should_add_space(prev_text, next_text):
    """Logic to determine where to add spaces to XML. Generally this is just
    as matter of checking for space characters, but there are some
    outliers"""
    prev_text, next_text = prev_text[-1:], next_text[:1]
    return (not prev_text.isspace() and not next_text.isspace()
            and next_text
            and prev_text not in '([/<'
            and next_text not in ').;,]>/')


def get_node_text(node, add_spaces=False):
    """ Extract all the text from an XML node (including the
    text of it's children). """
    node = deepcopy(node)
    # subscripts
    for e in node.xpath(".//E[@T='52']"):
        parent = e.getparent()
        prev_sib = e.getprevious()
        appending = "_{" + e.text + "} " + (e.tail or "")
        if prev_sib is not None:
            prev_sib.tail = (prev_sib.tail or '') + appending
        else:
            parent.text = (parent.text or '') + appending
        parent.remove(e)

    parts = [node.text] +\
        list(chain(*([c.text, c.tail] for c in node.getchildren()))) +\
        [node.tail]
    if add_spaces:
        final_text = ''
        for part in filter(bool, parts):
            if _should_add_space(final_text, part):
                final_text += " " + part
            else:
                final_text += part
        return final_text.strip()
    else:
        return ''.join(filter(None, parts))


def get_node_text_tags_preserved(node):
    """ Given an XML node, generate text from the node, skipping the PRTPAGE
    tag. """

    html_parser = HTMLParser.HTMLParser()

    if node.text:
        node_text = node.text
    else:
        node_text = ''

    for c in node:
        if c.tag == 'E':
            # xlmns non-sense makes me do this.
            e_tag = '<E T="03">%s</E>' % c.text
            node_text += e_tag
        if c.tail is not None:
            node_text += c.tail

    node_text = html_parser.unescape(node_text)
    return node_text

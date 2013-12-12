from itertools import takewhile
import logging

from regparser import utils
from regparser.citations import internal_citations, Label
import regparser.grammar.interpretation_headers as grammar
from regparser.tree.paragraph import ParagraphParser
from regparser.tree.struct import Node, treeify


#   Can only be preceded by white space or a start of line
interpParser = ParagraphParser(r"(?<![^\s])%s\.", Node.INTERP)


def build(text, part):
    """Create a tree representing the whole interpretation."""
    part = str(part)
    title, body = utils.title_body(text)
    segments = segment_by_header(body, part)

    if segments:
        children = [segment_tree(body[s:e], part, [part]) for s, e in segments]
        return Node(
            body[:segments[0][0]], treeify(children),
            [part, Node.INTERP_MARK], title, Node.INTERP)
    else:
        return Node(
            body, [], [part, Node.INTERP_MARK], title,
            Node.INTERP)


def segment_by_header(text, part):
    """Return a list of headers (section, appendices, paragraphs) and their
    offsets."""
    starts = [start for _, start, _ in grammar.parser.scanString(text)]
    starts = starts + [len(text)]

    offset_pairs = []
    for idx in range(1, len(starts)):
        offset_pairs.append((starts[idx-1], starts[idx]))

    return offset_pairs


def segment_tree(text, part, parent_label):
    """Build a tree representing the interpretation of a section, paragraph,
    or appendix."""
    title, body = utils.title_body(text)
    exclude = [(pc.full_start, pc.full_end) for pc in
               internal_citations(body, Label(part=parent_label[0]))]

    label = text_to_labels(title, part)[0]
    return interpParser.build_tree(body, 1, exclude, label, title)


def text_to_labels(text, part, warn=True):
    all_citations = internal_citations(text.strip(), Label(part=part))
    all_citations = sorted(all_citations, key=lambda c: c.start)
    #   We care only about the first citation and its clauses
    citations = all_citations[:1]
    if citations:
        if citations[0].in_clause:
            #   Clauses still in the first conjunction
            citations.extend(takewhile(lambda c: c.in_clause,
                                       all_citations[1:]))

        return [citation.label.to_list() + [Node.INTERP_MARK]
                for citation in citations]
    elif warn:
        logging.warning("Couldn't turn into label: " + text)
    return []

from regparser import utils
from regparser.grammar.internal_citations import comment_citation
import regparser.grammar.interpretation_headers as grammar
from regparser.tree.paragraph import ParagraphParser
from regparser.tree.struct import Node


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
            body[:segments[0][0]], children, [part, Node.INTERP_MARK],
            title, Node.INTERP)
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
    exclude = [(s, e) for _, s, e in comment_citation.scanString(body)]

    label = text_to_label(title, part)
    return interpParser.build_tree(body, 1, exclude, label, title)


def text_to_label(text, part):
    parsed = grammar.parser.parseString(text)
    if parsed.letter:
        #Appendix
        label = [part, parsed.letter]
    elif parsed.level1:
        #Paragraph
        label = [
            part, parsed.section, parsed.level1, parsed.level2,
            parsed.level3, parsed.level4, parsed.level5]
        while not label[-1]:
            #Remove training empty strings
            label.pop()
    else:
        #Section only
        label = [part, parsed.section]
    label = label + [Node.INTERP_MARK]
    return label

from parser import utils
from parser.grammar.internal_citations import comment_citation
from parser.tree import struct
from parser.tree.paragraph import ParagraphParser
from parser.tree.interpretation import carving


def _mk_label(old_label, next_part):
    return struct.extend_label(old_label, '-' + next_part, next_part)


#   Can only be preceded by white space or a start of line
interpParser = ParagraphParser(r"(?<![^\s])%s\.", _mk_label)


def build(text, part):
    """Create a tree representing the whole interpretation."""
    title, body = utils.title_body(text)
    label = struct.label("%d-Interpretations" % part, [str(part), 
        "Interpretations"],
            title)
    segments = carving.segment_by_header(body, part)

    if segments:
        children = []
        for start,end in segments:
            segment_text = body[start:end]
            children.append(segment_tree(segment_text, part, label))
        return struct.node(body[:segments[0][0]], children, label)
    else:
        return struct.node(body, [], label)


def segment_tree(text, part, parent_label):
    """Build a tree representing the interpretation of a section, paragraph,
    or appendix."""
    title, body = utils.title_body(text)
    exclude = [(s,e) for _,s,e in comment_citation.scanString(text)]

    label_text = carving.get_appendix_letter(title)
    if not label_text:
        label_text = carving.get_section_number(title, part)
    if not label_text:  #   Paragraph
        label_text = carving.build_label("", 
            carving.applicable_paragraph(title)
        )
    return interpParser.build_paragraph_tree(body, 1, exclude,
        label=struct.extend_label(parent_label, '-' + label_text, label_text, 
            title)
    )

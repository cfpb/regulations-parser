from parser import utils
from parser.grammar.internal_citations import comment_citation
from parser.tree import struct
from parser.tree.paragraph import ParagraphParser
from parser.tree.interpretation import carving


def _mk_label(old_label, next_part):
    return struct.extend_label(old_label, '-' + next_part, next_part)
#   Can only be preceded by white space or a start of line


interpParser = ParagraphParser(r"(?<![^\s])%s\.", _mk_label)


def appendix_tree(text, label):
    """Build a tree representing an appendix interpretation (as opposed to
    an interpretation of a section)."""
    title, body = utils.title_body(text)
    label_text = carving.get_appendix_letter(title)
    exclude = [(start,end) for _,start,end in
            comment_citation.scanString(body)]
    return interpParser.build_paragraph_tree(body, 1,
            exclude,
            label=struct.extend_label(label, '-' + label_text, label_text, 
                title)
            )


def build(text, part):
    """Create a tree representing the whole interpretation."""
    title, body = utils.title_body(text)
    label = struct.label("%d-Interpretations" % part, [str(part), 
        "Interpretations"],
            title)
    appendix_offsets = carving.appendices(body)
    appendices = []
    if appendix_offsets:
        for start, end in appendix_offsets:
            appendices.append(appendix_tree(body[start:end], label))
        body = body[:appendix_offsets[0][0]]

    sections = carving.sections(body, part)
    if sections:
        children = []
        for start, end in sections:
            section_text = body[start:end]
            children.append(section_tree(section_text, part, label))
        return struct.node(body[:sections[0][0]], children + appendices, 
                label)
    else:
        return struct.node(body, appendices, label)


def section_tree(text, part, parent_label):
    """Tree representing a single section within the interpretation."""
    title, body = utils.title_body(text)
    section = carving.get_section_number(title, part)
    offsets = carving.applicable_offsets(body, section)
    label = struct.extend_label(parent_label, "-" + section, section, title)
    if offsets:
        children = []
        for start, end in offsets:
            applicable_text = body[start:end]
            children.append(applicable_tree(applicable_text, section, label))
        return struct.node(body[:offsets[0][0]], children, label)
    else:
        return struct.node(body, label=label)


def applicable_tree(text, section, parent_label):
    """Tree representing all of the text applicable to a single paragraph."""
    paragraph_header, body = utils.title_body(text)
    label_text = carving.build_label("", 
            carving.applicable_paragraph(paragraph_header, section))
    exclude = [(start,end) for _,start,end in
            comment_citation.scanString(body)]
    return interpParser.build_paragraph_tree(body, 1, exclude,
            label=struct.extend_label(parent_label, label_text, label_text,
                paragraph_header))

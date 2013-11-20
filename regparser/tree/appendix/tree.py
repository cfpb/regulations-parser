from regparser import utils
from regparser.citations import internal_citations, Label
from regparser.tree.appendix import carving, generic
from regparser.tree.paragraph import ParagraphParser
from regparser.tree.struct import Node
import string

parParser = ParagraphParser(r"\(%s\)", Node.APPENDIX)


def trees_from(text, part, parent_label):
    """Build a tree for the appendix section. It will have children for each
    appendix. Text is the text of the entire regulation, while part is the
    regulation's part (e.g. 1520.)"""
    children = []
    for begin, end in carving.appendices(text):
        title, appendix = utils.title_body(text[begin:end])
        appendix_letter = carving.get_appendix_letter(title, part)
        label = parent_label + [appendix_letter]
        sections = carving.appendix_sections(appendix, appendix_letter)
        if sections:
            child = paragraph_tree(
                appendix_letter, sections, appendix, label, title)
        else:
            child = generic_tree(appendix, label, title)
        children.append(child)
    return children


def letter_for(index):
    """Convert an index into a letter (or letter pair). a-z, then aa-az-zz"""
    if index < 26:
        return string.ascii_lowercase[index]
    return (string.ascii_lowercase[(index // 26) - 1]  # First letter in pair
            + string.ascii_lowercase[index % 26])      # Second letter


def generic_tree(text, label, title=None):
    """Use the "generic" parser to build a tree. The "generic" parser simply
    splits on Title Case and treats body text as the node content."""
    segments = generic.segments(text)
    if not segments:
        return Node(text, label=label, title=title, node_type=Node.APPENDIX)

    children = []
    for index, seg in enumerate(segments):
        start, end = seg
        seg_title, body = utils.title_body(text[start:end])
        label_character = letter_for(index)
        children.append(
            Node(body, label=(
                label + [label_character]),
                title=seg_title, node_type=Node.APPENDIX))

    return Node(text[:segments[0][0]], children, label, title, Node.APPENDIX)


def paragraph_tree(appendix_letter, sections, text, label, title=None):
    """Use the paragraph parser to parse through each section in this
    appendix."""
    if not sections:
        return Node(text, label=label, title=title, node_type=Node.APPENDIX)
    children = []
    for begin, end in sections:
        seg_title, section_text = utils.title_body(text[begin:end])
        sec_num = carving.get_appendix_section_number(
            seg_title, appendix_letter)
        exclude = [(pc.full_start, pc.full_end) for pc in
                   internal_citations(section_text, Label(part=label[0]))]

        child = parParser.build_tree(
            section_text, exclude=exclude, label=label + [sec_num],
            title=seg_title)

        children.append(child)
    return Node(text[:sections[0][0]], children, label, title, Node.APPENDIX)

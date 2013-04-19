from parser import utils
from parser.grammar.internal_citations import regtext_citation
from parser.tree import struct
from parser.tree.appendix import carving, generic
from parser.tree.section import regParser
import string


def trees_from(text, part, parent_label):
    """Build a tree for the appendix section. It will have children for each
    appendix. Text is the text of the entire regulation, while part is the
    regulation's part (e.g. 1520.)"""
    children = []
    for begin, end in carving.appendices(text):
        title, appendix = utils.title_body(text[begin:end])
        appendix_letter = carving.get_appendix_letter(title, part)
        label = struct.extend_label(parent_label, "-" + appendix_letter,
                appendix_letter, title)
        sections = carving.appendix_sections(appendix, appendix_letter)
        if sections:
            child = paragraph_tree(appendix_letter, sections, appendix, label)
        else:
            child = generic_tree(appendix, label)
        children.append(child)
    return children


def generic_tree(text, label):
    """Use the "generic" parser to build a tree. The "generic" parser simply
    splits on Title Case and treats body text as the node content."""
    segments = generic.segments(text)
    if not segments:
        return struct.node(text, label=label)

    children = []
    for index, seg in enumerate(segments):
        start, end = seg
        seg_title, body = utils.title_body(text[start:end])
        label_character = string.ascii_lowercase[index]
        children.append(struct.node(body, label=struct.extend_label(label,
            "-" + label_character, label_character, seg_title)))
    return struct.node(text[:segments[0][0]], children, label)


def paragraph_tree(appendix_letter, sections, text, label):
    """Use the paragraph parser to parse through each section in this
    appendix."""
    if not sections:
        return struct.node(text, label=label)
    children = []
    for begin, end in sections:
        title, section_text = utils.title_body(text[begin:end])
        sec_num = carving.get_appendix_section_number(title, appendix_letter)
        exclude = [(start, end) for _, start, end in
                regtext_citation.scanString(section_text)]
        child = regParser.build_paragraph_tree(section_text, 
                exclude=exclude,
                label=struct.extend_label(label, "-" + sec_num, sec_num, title))
        children.append(child)
    return struct.node(text[:sections[0][0]], children, label)

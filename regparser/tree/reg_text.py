from regparser import utils
from regparser.tree import struct
from regparser.tree.section import build_section_tree, sections

def build_reg_text_tree(text, part):
    """Build up the whole tree from the plain text of a single
    regulation."""
    title, body = utils.title_body(text)
    lab = struct.label(str(part), [str(part)], title)

    sects = sections(body, part)
    if not sects:
        return struct.node(text, label=lab)
    children_text = body[:sects[0][0]]

    children = []
    for start,end in sects:
        section_text = body[start:end]
        children.append(build_section_tree(section_text, part))
    return struct.node(children_text, children, lab)

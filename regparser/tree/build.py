# vim: set encoding=utf-8
from regparser.tree.appendix.tree import trees_from as appendix_trees
from regparser.tree.interpretation import build as build_interp_tree
from regparser.tree.reg_text import build_reg_text_tree
from regparser.tree.supplement import find_supplement_start
import re


def find_cfr_part(text):
    """Figure out what CFR this is referring to from the text."""
    for match in re.finditer(ur"^PART (\d+)[-—\w]", text):
        return int(match.group(1))


def build_whole_regtree(text):
    """Combine the output of numerous functions to get to a whole regulation
    tree."""
    part = find_cfr_part(text)
    reg_tree = build_reg_text_tree(text, part)
    appendices = appendix_trees(text, part, reg_tree.label)

    reg_tree.children.extend(appendices)
    supplement_start = find_supplement_start(text)
    if supplement_start is not None:
        interps = build_interp_tree(text[supplement_start:], part)
        reg_tree.children.append(interps)
    return reg_tree

from regparser.tree.appendix.tree import trees_from as appendix_trees
from regparser.tree.interpretation import build as build_interp_tree
from regparser.tree.reg_text import build_reg_text_tree
from regparser.tree.supplement import find_supplement_start
import re

def find_cfr_part(text):
    """Figure out what CFR this is referring to from the text."""
    counts = {}
    for match in re.finditer(ur"(\d+)\.(\d+)", text):
        counts[match.group(1)] = counts.get(match.group(1), 0) + 1
    best, best_count = None, 0
    for part in counts:
        if counts[part] > best_count:
            best = part
            best_count = counts[part]
    return int(best)

def build_whole_regtree(text):
    """Combine the output of numerous functions to get to a while regulation
    tree."""
    interp = text[find_supplement_start(text):]

    part = find_cfr_part(text)
    reg_tree = build_reg_text_tree(text, part)
    interps = build_interp_tree(interp, part)
    appendices = appendix_trees(text, part, reg_tree.label)

    reg_tree.children.extend(appendices)
    reg_tree.children.append(interps)
    return reg_tree

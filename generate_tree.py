import codecs
import json
from parser.tree.appendix.tree import trees_from as appendix_trees
from parser.tree.interpretation.tree import build as build_interp_tree
from parser.tree.reg_text import build_reg_text_tree
from parser.tree.supplement import find_supplement_start

if __name__ == "__main__":
    with codecs.open('rege.txt', encoding='utf-8') as f:
        reg = unicode(f.read())

    interp = reg[find_supplement_start(reg):]

    reg_tree = build_reg_text_tree(reg, 1005)
    interp_tree = build_interp_tree(interp, 1005)
    appendix_trees = appendix_trees(reg, 1005, reg_tree['label'])

    reg_tree['children'].extend(appendix_trees)
    reg_tree['children'].append(interp_tree)

    print json.dumps(reg_tree)

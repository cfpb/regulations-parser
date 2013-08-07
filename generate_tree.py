import codecs
import sys

from regparser.tree.appendix.tree import trees_from as appendix_trees
from regparser.tree.interpretation import build as build_interp_tree
from regparser.tree.reg_text import build_reg_text_tree
from regparser.tree.struct import NodeEncoder
from regparser.tree.supplement import find_supplement_start

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage: python generate_tree.py path/to/reg.txt part"
        print " e.g.: python generate_tree.py rege.txt 1005"
        exit()
    with codecs.open(sys.argv[1], encoding='utf-8') as f:
        reg = unicode(f.read())

    interp = reg[find_supplement_start(reg):]

    part = int(sys.argv[2])
    reg_tree = build_reg_text_tree(reg, part)
    interp_tree = build_interp_tree(interp, part)
    appendix_trees = appendix_trees(reg, part, reg_tree.label)

    reg_tree.children.extend(appendix_trees)
    reg_tree.children.append(interp_tree)

    print NodeEncoder().encode(reg_tree)

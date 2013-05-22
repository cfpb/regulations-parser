import json
from parser.tree import xml_tree

tree = xml_tree.build_tree()

print json.dumps(tree)



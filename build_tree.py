import json
from parser.tree.xml_parser import reg_text

reg_xml_file = '/vagrant/data/regulations/regulation/1005.xml'
reg_xml = open(reg_xml_file, 'r').read()

tree = reg_text.build_tree(reg_xml)

print json.dumps(tree)



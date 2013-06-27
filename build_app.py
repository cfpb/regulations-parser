import json
from parser.tree.xml_parser import appendices

reg_xml_file = '/vagrant/data/regulations/regulation/rege-2011-31725.xml'
reg_xml = open(reg_xml_file, 'r').read()

tree = appendices.build_non_reg_text(reg_xml)
print json.dumps(tree)

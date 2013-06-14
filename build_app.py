from parser.tree import xml_appendices

reg_xml_file = '/vagrant/data/regulations/regulation/1005.xml'
reg_xml = open(reg_xml_file, 'r').read()

tree = xml_appendices.build_tree(reg_xml)

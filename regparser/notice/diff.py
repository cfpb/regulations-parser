#vim: set encoding=utf-8
import re

from lxml import etree

from regparser.tree import struct
from regparser.tree.xml_parser.reg_text import build_section

def clear_between(xml_node, start_char, end_char):
    as_str = etree.tostring(xml_node, encoding=unicode)
    start_char, end_char = re.escape(start_char), re.escape(end_char)
    pattern = re.compile(start_char + '[^' + end_char + ']*' + end_char, 
            re.M + re.S + re.U)
    return etree.fromstring(pattern.sub('', as_str))


def remove_char(xml_node, char):
    as_str = etree.tostring(xml_node, encoding=unicode)
    return etree.fromstring(as_str.replace(char, ''))
    

def find_diffs(xml_tree):
    """Find the XML nodes that are needed to determine diffs"""
    regtexts = xml_tree.xpath('//REGTEXT')
    last_context = None
    diffs = []
    for section in xml_tree.xpath('//SECTION'):
        section = clear_between(section, '[', ']')
        section = remove_char(remove_char(section, u'▸'), u'◂')
        node = build_section('1005', section)
        if node:
            def per_node(node):
                print node['label']['parts']
            struct.walk(node, per_node)

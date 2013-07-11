#vim: set encoding=utf-8
import re

from lxml import etree

from regparser.tree import struct
from regparser.tree.xml_parser.reg_text import build_section

def clear_between(xml_node, start_char, end_char):
    """Gets rid of any content (including xml nodes) between chars"""
    as_str = etree.tostring(xml_node, encoding=unicode)
    start_char, end_char = re.escape(start_char), re.escape(end_char)
    pattern = re.compile(start_char + '[^' + end_char + ']*' + end_char, 
            re.M + re.S + re.U)
    return etree.fromstring(pattern.sub('', as_str))


def remove_char(xml_node, char):
    """Remove from this node and all its children"""
    as_str = etree.tostring(xml_node, encoding=unicode)
    return etree.fromstring(as_str.replace(char, ''))
    

def find_diffs(xml_tree):
    """Find the XML nodes that are needed to determine diffs"""
    last_context = None
    diffs = []
    #   Only final notices have this format
    for section in xml_tree.xpath('//REGTEXT/SECTION'):
        section = clear_between(section, '[', ']')
        section = remove_char(remove_char(section, u'▸'), u'◂')
        node = build_section('1005', section)
        if node:
            def per_node(node):
                if node_is_empty(node):
                    for c in node['children']:
                        per_node(c)
                else:
                    print node['label']['parts'], node['text']
            per_node(node)

def node_is_empty(node):
    """Handle different ways the regulation represents no content"""
    return node['text'].strip() == ''

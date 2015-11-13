import re

from regparser.layer.layer import Layer
from regparser.tree import struct
from regparser.tree.priority_stack import PriorityStack
from regparser.tree.xml_parser import tree_utils


class HeaderStack(PriorityStack):
    """Used to determine Table Headers -- indeed, they are complicated
    enough to warrant their own stack"""
    def unwind(self):
        children = [pair[1] for pair in self.pop()]
        self.peek_last()[1].children = children


class TableHeaderNode(object):
    """Represents a cell in a table's header"""
    def __init__(self, text, level):
        self.text = text
        self.level = level
        self.children = []

    def height(self):
        child_heights = [0] + [c.height() for c in self.children]
        return 1 + max(child_heights)

    def width(self):
        if not self.children:
            return 1
        return sum(c.width() for c in self.children)


def build_header(xml_nodes):
    """Builds a TableHeaderNode tree, with an empty root. Each node in the tree
    includes its colspan/rowspan"""
    stack = HeaderStack()
    stack.add(0, TableHeaderNode(None, 0))  # Root
    for xml_node in xml_nodes:
        level = int(xml_node.attrib['H'])
        text = tree_utils.get_node_text(xml_node, add_spaces=True).strip()
        stack.add(level, TableHeaderNode(text, level))

    while stack.size() > 1:
        stack.unwind()
    root = stack.m_stack[0][0][1]

    max_height = root.height()

    def set_rowspan(n):
        n.rowspan = max_height - n.height() - n.level + 1
    struct.walk(root, set_rowspan)

    def set_colspan(n):
        n.colspan = n.width()
    struct.walk(root, set_colspan)

    return root


def table_xml_to_plaintext(xml_node):
    """Markdown representation of a table. Note that this doesn't account
    for all the options needed to display the table properly, but works fine
    for simple tables. This gets included in the reg plain text"""
    header = [tree_utils.get_node_text(hd, add_spaces=True).strip()
              for hd in xml_node.xpath('./BOXHD/CHED')]
    divider = ['---']*len(header)
    rows = []
    for tr in xml_node.xpath('./ROW'):
        rows.append([tree_utils.get_node_text(td, add_spaces=True).strip()
                     for td in tr.xpath('./ENT')])
    table = []
    for row in [header] + [divider] + rows:
        table.append('|' + '|'.join(row) + '|')
    return '\n'.join(table)


def table_xml_to_data(xml_node):
    """Construct a data structure of the table data. We provide a different
    structure than the native XML as the XML encodes too much logic. This
    structure can be used to generate semi-complex tables which could not be
    generated from the markdown above"""
    header_root = build_header(xml_node.xpath('./BOXHD/CHED'))
    header = [[] for _ in range(header_root.height())]

    def per_node(node):
        header[node.level].append({'text': node.text,
                                   'colspan': node.colspan,
                                   'rowspan': node.rowspan})
    struct.walk(header_root, per_node)
    header = header[1:]     # skip the root

    rows = []
    for row in xml_node.xpath('./ROW'):
        rows.append([tree_utils.get_node_text(td, add_spaces=True).strip()
                     for td in row.xpath('./ENT')])

    return {'header': header, 'rows': rows}


class Formatting(Layer):
    fenced_re = re.compile(r"```(?P<type>[a-zA-Z0-9 ]+)\w*\n"
                           + r"(?P<lines>([^\n]*\n)+)"
                           + r"```")
    subscript_re = re.compile(r"([a-zA-Z0-9]+)_\{(\w+)\}")
    dashes_re = re.compile(r"_{5,}$")

    def process(self, node):
        layer_el = []
        if node.source_xml is not None:
            if node.source_xml.tag == 'GPOTABLE':
                tables = [node.source_xml]
            else:
                tables = []
            tables.extend(node.source_xml.xpath('.//GPOTABLE'))
            for table in tables:
                layer_el.append({'text': table_xml_to_plaintext(table),
                                 'locations': [0],
                                 'table_data': table_xml_to_data(table)})

        for match in Formatting.fenced_re.finditer(node.text):
            layer_el.append({
                'text': node.text[match.start():match.end()],
                'locations': [0],
                'fence_data': {
                    'type': match.group('type'),
                    'lines': filter(bool, match.group('lines').split("\n"))}})

        subscripts = {}
        for match in Formatting.subscript_re.finditer(node.text):
            key = (match.group(1), match.group(2))
            subscripts[key] = subscripts.get(key, 0) + 1
        for key, count in subscripts.iteritems():
            variable, subscript = key
            layer_el.append({
                'text': variable + '_{' + subscript + '}',
                'locations': list(range(count)),
                'subscript_data': {'variable': variable,
                                   'subscript': subscript}})

        for match in Formatting.dashes_re.finditer(node.text):
            layer_el.append({
                'text': node.text,
                'locations': [0],
                'dash_data': {
                    'text': node.text[:match.start()],
                },
            })

        if layer_el:
            return layer_el

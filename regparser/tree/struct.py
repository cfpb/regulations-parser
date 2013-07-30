from json import JSONEncoder


def label(text="", parts=[], title=None):
    if title:
        return {'text': text, 'parts': parts, 'title': title}
    return {'text': text, 'parts': parts}
_label = label


def extend_label(existing, text, part, title=None):
    return label(existing['text'] + text, existing['parts'] + [part], title)


def node(text='', children=[], label=None):
    if not label:
        label = _label('',[])
    return {'text': text, 'children': children, 'label': label}


class Node:
    INTERP = 'interp'

    def __init__(self, typ, text='', children=[], label=[], title=None):
        self.typ = typ
        self.text = text
        self.children = list(children)  #   defensive copy
        self.label = [l for l in label if l != '']
        title = title or None
        self.title = title
    def __repr__(self):
        return ("%s( typ = %s, text = %s, children = %s, label = %s, "
            + "title = %s)" % (type(self.typ), repr(self.text), 
                repr(self.children), repr(self.label), repr(self.title)))


class NodeEncoder(JSONEncoder):
    """Custom JSON encoder to handle Node objects"""
    def default(self, obj):
        if isinstance(obj, Node):
            fields = dict(obj.__dict__)
            if obj.title is None:
                del fields['title']
            return fields
        return JSONEncoder.default(self, obj)


def walk(node, fn):
    """Perform fn for every node in the tree. Pre-order traversal. fn must
    be a function that accepts a root node."""
    result = fn(node)
    if result != None:
        results = [result]
    else:
        results = []
    for child in node['children']:
        results += walk(child, fn)
    return results


def find(root, label):
    """Search through the tree to find the node with this label."""
    def check(node):
        if node['label']['text'] == label:
            return node
    response = walk(root, check)
    if response:
        return response[0]


def join_text(node):
    """Join the text of this node and all children"""
    bits = []
    walk(node, lambda n: bits.append(n['text']))
    return ''.join(bits)

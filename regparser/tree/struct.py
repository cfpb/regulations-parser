from json import JSONEncoder

class Node:
    APPENDIX = 'appendix'
    INTERP = 'interp'
    REGTEXT = 'regtext'

    def __init__(self, text='', children=[], label=[], title=None, 
            typ='regtext'):
        self.text = unicode(text)
        self.children = list(children)  #   defensive copy
        self.label = [str(l) for l in label if l != '']
        title = title or None
        self.title = title
        self.typ = typ
    def __repr__(self):
        return (("Node( text = %s, children = %s, label = %s, title = %s, "
            + "typ = %s)") % (repr(self.text), repr(self.children), 
                repr(self.label), repr(self.title), repr(self.typ)))
    def __cmp__(self, other):
        return cmp(repr(self), repr(other))
    def label_id(self):
        return '-'.join(self.label)


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
    for child in node.children:
        results += walk(child, fn)
    return results


def find(root, label):
    """Search through the tree to find the node with this label."""
    def check(node):
        if node.label_id() == label:
            return node
    response = walk(root, check)
    if response:
        return response[0]


def join_text(node):
    """Join the text of this node and all children"""
    bits = []
    walk(node, lambda n: bits.append(n.text))
    return ''.join(bits)

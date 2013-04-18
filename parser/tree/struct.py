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

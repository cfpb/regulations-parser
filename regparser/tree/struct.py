from collections import defaultdict
from json import JSONEncoder

import logging
import hashlib


class Node(object):
    APPENDIX = u'appendix'
    INTERP = u'interp'
    REGTEXT = u'regtext'
    SUBPART = u'subpart'
    EMPTYPART = u'emptypart'

    INTERP_MARK = 'Interp'

    def __init__(self, text='', children=[], label=[], title=None,
                 node_type=REGTEXT, source_xml=None, tagged_text=''):

        self.text = unicode(text)

        # defensive copy
        self.children = list(children)

        self.label = [unicode(l) for l in label if l != '']
        title = unicode(title or '')
        self.title = title or None
        self.node_type = node_type
        self.source_xml = source_xml
        self.marker = None
        self.tagged_text = tagged_text

    def __repr__(self):
        return (("Node(text=%s, label=%s, title=%s, marker=%s, "
                + "node_type=%s, children=%s)") % (
                    repr(self.text),
                    repr(self.label),
                    repr(self.title),
                    repr(self.marker),
                    repr(self.node_type),
                    repr(self.children)
        ))

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
            if obj.marker is None:
                del fields['marker']
            for field in ('tagged_text', 'source_xml', 'child_labels'):
                if field in fields:
                    del fields[field]
            return fields
        return super(NodeEncoder, self).default(obj)


def node_decode_hook(d):
    """Convert a JSON object into a Node"""
    if set(
            ('text', 'children',
                'label', 'node_type')) - set(d.keys()) == set():

        return Node(
            d['text'], d['children'], d['label'],
            d.get('title', None), d['node_type'])
    else:
        return d


def walk(node, fn):
    """Perform fn for every node in the tree. Pre-order traversal. fn must
    be a function that accepts a root node."""
    result = fn(node)

    if result is not None:
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
    else:
        logging.warning('Failed to locate node with label {}'.format(label))
        return None


def join_text(node):
    """Join the text of this node and all children"""
    bits = []
    walk(node, lambda n: bits.append(n.text))
    return ''.join(bits)


def merge_duplicates(nodes):
    """Given a list of nodes with the same-length label, merge any
    duplicates (by combining their children)"""
    found_pair = None
    for lidx, lhs in enumerate(nodes):
        for ridx, rhs in enumerate(nodes[lidx + 1:], lidx + 1):
            if lhs.label == rhs.label:
                found_pair = (lidx, ridx)
    if found_pair:
        lidx, ridx = found_pair
        lhs, rhs = nodes[lidx], nodes[ridx]
        lhs.children.extend(rhs.children)
        return merge_duplicates(nodes[:ridx] + nodes[ridx + 1:])
    else:
        return nodes


def treeify(nodes):
    """Given a list of nodes, convert those nodes into the appropriate tree
    structure based on their labels. This assumes that all nodes will fall
    under a set of 'root' nodes, which have the min-length label."""
    if not nodes:
        return nodes

    min_len, with_min = len(nodes[0].label), []

    for node in nodes:
        if len(node.label) == min_len:
            with_min.append(node)
        elif len(node.label) < min_len:
            min_len = len(node.label)
            with_min = [node]
    with_min = merge_duplicates(with_min)

    roots = []
    for root in with_min:
        if root.label[-1] == Node.INTERP_MARK:
            is_child = lambda n: n.label[:len(root.label)-1] == root.label[:-1]
        else:
            is_child = lambda n: n.label[:len(root.label)] == root.label
        children = [n for n in nodes if n.label != root.label and is_child(n)]
        root.children = root.children + treeify(children)
        roots.append(root)
    return roots


class FrozenNode(object):
    """Immutable interface for nodes. No guarantees about internal state."""
    _pool = defaultdict(set)    # collection of all FrozenNodes, keyed by hash

    def __init__(self, text='', children=(), label=(), title='',
                 node_type=Node.REGTEXT, tagged_text=''):
        self._text = text or ''
        self._children = tuple(children)
        self._label = tuple(label)
        self._title = title or ''
        self._node_type = node_type
        self._tagged_text = tagged_text or ''
        self._hash = self._generate_hash()
        FrozenNode._pool[self.hash].add(self)

    @property
    def text(self):
        return self._text

    @property
    def children(self):
        return self._children

    @property
    def label(self):
        return self._label

    @property
    def title(self):
        return self._title

    @property
    def node_type(self):
        return self._node_type

    @property
    def tagged_text(self):
        return self._tagged_text

    @property
    def hash(self):
        return self._hash

    def _generate_hash(self):
        """Called during instantiation. Digests all fields"""
        hasher = hashlib.sha256()
        hasher.update(self.text.encode('utf-8'))
        hasher.update(self.tagged_text.encode('utf-8'))
        hasher.update(self.title.encode('utf-8'))
        hasher.update(self.label_id.encode('utf-8'))
        hasher.update(self.node_type)
        for child in self.children:
            hasher.update(child.hash)
        return hasher.hexdigest()

    def __hash__(self):
        """As the hash property is already distinctive, re-use it"""
        return hash(self.hash)

    def __eq__(self, other):
        """We define equality as having the same fields except for children.
        Instead of recursively inspecting them, we compare only their hash
        (this is a Merkle tree)"""
        return (other.__class__ == self.__class__
                and self.hash == other.hash
                # Compare the fields to limit the effect of hash collisions
                and self.text == other.text
                and self.title == other.title
                and self.node_type == other.node_type
                and self.tagged_text == other.tagged_text
                and self.label_id == other.label_id
                and [c.hash for c in self.children] ==
                    [c.hash for c in other.children])

    @staticmethod
    def from_node(node):
        """Convert a struct.Node (or similar) into a struct.FrozenNode. This
        also checks if this node has already been instantiated. If so, it
        returns the instantiated version (i.e. only one of each identical node
        exists in memory)"""
        children = map(FrozenNode.from_node, node.children)
        fresh = FrozenNode(text=node.text, children=children, label=node.label,
                           title=node.title or '', node_type=node.node_type,
                           tagged_text=getattr(node, 'tagged_text', '') or '')
        for el in FrozenNode._pool[fresh.hash]:
            if el == fresh:
                return el   # note we are _not_ returning fresh

    @property
    def label_id(self):
        """Convert label into a string"""
        if not hasattr(self, '_label_id'):
            self._label_id = '-'.join(self.label)
        return self._label_id

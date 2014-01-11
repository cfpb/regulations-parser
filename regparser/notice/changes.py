import logging
import copy
from collections import defaultdict

from regparser.tree import struct
from regparser.diff.treediff import node_to_dict


def find_candidate(root, label_last):
    """
        Look through the tree for a node that has the same paragraph marker as
        the one we're looking for (and also has no children).  That might be a
        mis-parsed node. Because we're parsing partial sections in the notices,
        it's likely we might not be able to disambiguate between paragraph
        markers.
    """
    def check(node):
        if node.label[-1] == label_last and node.children == []:
            return node
    response = struct.walk(root, check)
    return response


def resolve_candidates(amend_map, warn=True):
    """Ensure candidate isn't actually accounted for elsewhere, and fix
    it's label. """

    for label, node in amend_map.items():
        if 'node' in node:
            node_label = node['node'].label_id()
            if node['candidate']:
                if node_label not in amend_map:
                    node['node'].label = label.split('-')
                else:
                    del amend_map[label]
                    if warn:
                        mesg = 'Unable to match amendment'
                        mesg += ' to change for: %s ' % label
                        logging.warning(mesg)


def find_misparsed_node(section_node, label):
    candidates = find_candidate(section_node, label[-1])
    if len(candidates) == 1:
        candidate = candidates[0]
        return {
            'action': 'updated',
            'node': candidate,
            'candidate': True}


def match_labels_and_changes(amendments, section_node):
    amend_map = {}
    for amend in amendments:
        if amend.action == 'MOVE':
            change = {'action': amend.action, 'destination': amend.destination}
            amend_map[amend.label_id()] = change
            print "MOVE: %s " % amend.label_id()
        elif amend.action == 'DELETE':
            amend_map[amend.label_id()] = {'action': amend.action}
        else:
            node = struct.find(section_node, amend.label_id())
            if node is None:
                candidate = find_misparsed_node(section_node, amend.label)
                if candidate:
                    amend_map[amend.label_id()] = candidate
            else:
                if amend.label_id() == '1005-33-c-2-iii':
                    print "OOPS: %s " % amend.action
                    print node
                amend_map[amend.label_id()] = {
                    'node': node,
                    'action': amend.action,
                    'candidate': False}
            if amend.field is not None:
                amend_map[amend.label_id()]['field'] = amend.field

    resolve_candidates(amend_map)
    for l, a in amend_map.items():
        print l, a['action']
    return amend_map

def format_node(node, amendment):
    """ Format a node into a dict, and add in amendment information. """
    node_as_dict = {
        'node': node_to_dict(node),
        'action': amendment['action'],
    }

    if 'extras' in amendment:
        node_as_dict.update(amendment['extras'])

    if 'field' in amendment:
        node_as_dict['field'] = amendment['field']
    return {node.label_id(): node_as_dict}


def create_field_amendment(label, amendment):
    """ If an amendment is changing just a field (text, title) then we 
    don't need to package the rest of the paragraphs with it. Those get 
    dealt with later, if appropriate. """

    nodes_list = []
    flatten_tree(nodes_list, amendment['node'])

    changed_nodes = [n for n in nodes_list if n.label_id() == label]
    nodes = [format_node(n, amendment) for n in changed_nodes]
    return nodes

def create_add_amendment(amendment):
    """ An amendment comes in with a whole tree structure. We break apart the
    tree here (this is what flatten does), convert the Node objects to JSON
    representations. This ensures that each amendment only acts on one node.
    """

    nodes_list = []
    flatten_tree(nodes_list, amendment['node'])
    nodes = [format_node(n, amendment) for n in nodes_list]
    return nodes


def create_subpart_amendment(subpart_node):
    """ Create an amendment that describes a subpart. In particular
    when the list of nodes added gets flattened, each node specifies which
    subpart it's part of. """

    amendment = {
        'node': subpart_node,
        'action': 'POST',
        'extras': {'subpart': subpart_node.label}
    }
    return create_add_amendment(amendment)


def flatten_tree(node_list, node):
    """ Flatten a tree, removing all hierarchical information, making a
    list out of all the nodes. """
    for c in node.children:
        flatten_tree(node_list, c)

    #Don't be destructive.
    no_kids = copy.deepcopy(node)
    no_kids.children = []
    node_list.append(no_kids)


def remove_intro(l):
    """ Remove the marker that indicates this is a change to introductory
    text. """
    return l.replace('[text]', '')


class NoticeChanges(object):
    """ Notice changes. """
    def __init__(self):
        self.changes = defaultdict(list)

    def update(self, changes):
        """ Essentially add more changes into NoticeChanges. This is
        cognizant of the fact that a single label can have more than
        one change. """
        for l, c in changes.items():
            self.changes[l].append(c)

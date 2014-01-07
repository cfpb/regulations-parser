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
        elif amend.action == 'DELETE':
            amend_map[amend.label_id()] = {'action': amend.action}
        else:
            node = struct.find(section_node, amend.label_id())
            if node is None:
                candidate = find_misparsed_node(section_node, amend.label)
                if candidate:
                    amend_map[amend.label_id()] = candidate
            else:
                amend_map[amend.label_id()] = {
                    'node': node,
                    'action': amend.action,
                    'candidate': False}
            if amend.field is not None:
                amend_map[amend.label_id()]['field'] = amend.field

    resolve_candidates(amend_map)
    return amend_map


def create_add_amendment(amendment):
    nodes_list = []
    flatten_tree(nodes_list, amendment['node'])

    def format_node(node):
        node_as_dict = {
            'node': node_to_dict(n),
            'action': amendment['action'],
        }

        if 'field' in amendment:
            node_as_dict['field'] = amendment['field']
        return {node.label_id(): node_as_dict}

        #node_as_dict = node_to_dict(n)
        #node_as_dict['action'] = amendment['action']

        #if 'field' in amendment:
        #    node_as_dict['field'] = amendment['field']
        #return {node.label_id(): node_as_dict}

    nodes = [format_node(n) for n in nodes_list]
    return nodes


def create_subpart_amendment(subpart_node):
    amendment = {
        'node': subpart_node,
        'action': 'POST'
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
    def __init__(self):
        self.changes = defaultdict(list)

    def update(self, changes):
        for l, c in changes.items():
            self.changes[l].append(c)

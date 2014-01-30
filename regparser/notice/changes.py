""" This module contains functions to help parse the changes in a notice.
Changes are the exact details of how the pargraphs, sections etc. in a
regulation have changed.  """

import logging
import copy
from collections import defaultdict

from regparser.tree import struct
from regparser.tree.paragraph import p_levels
from regparser.diff.treediff import node_to_dict


def bad_label(node):
    """ Look through a node label, and return True if it's a badly formed
    label. We can do this because we know what type of character should up at
    what point in the label. """

    if node.node_type == struct.Node.REGTEXT:
        for i, l in enumerate(node.label):
            if i == 0 and not l.isdigit():
                return True
            elif i == 1 and not l.isdigit():
                return True
            elif i > 1 and l not in p_levels[i-2]:
                return True
    return False

def impossible_label(n, amended_labels):
    """ Return True if n is not in the same family as amended_labels. """
    for l in amended_labels:
        if n.label_id().startswith(l):
            return False
    return True

def find_candidate(root, label_last, amended_labels):
    """
        Look through the tree for a node that has the same paragraph marker as
        the one we're looking for (and also has no children).  That might be a
        mis-parsed node. Because we're parsing partial sections in the notices,
        it's likely we might not be able to disambiguate between paragraph
        markers.
    """
    def check(node):
        """ Match last part of label."""
        if node.label[-1] == label_last:
            return node

    candidates = struct.walk(root, check)
    if len(candidates) > 1:
        # Look for mal-formed labels, labels that can't exist (because we're
        # not amending that part of the reg, or eventually a parent with no
        # children. 

        bad_labels = [n for n in candidates if bad_label(n)]
        impossible_labels = [n for n in candidates 
                             if impossible_label(n, amended_labels)]
        no_children = [n for n in candidates if n.children == []]

        #If we have a single option in any of the categories, return that. 
        if len(bad_labels) == 1:
            return bad_labels
        elif len(impossible_labels) == 1:
            return impossible_labels
        elif len(no_children) == 1:
            return no_children
    return candidates


def resolve_candidates(amend_map, warn=True):
    """Ensure candidate isn't actually accounted for elsewhere, and fix
    it's label. """
    for label, nodes in amend_map.items():
        for node in filter(lambda n: 'node' in n and n['candidate'], nodes):
            node_label = node['node'].label_id()
            if node_label not in amend_map:
                node['node'].label = label.split('-')
            elif label in amend_map:
                del amend_map[label]
                if warn:
                    mesg = 'Unable to match amendment to change for: %s'
                    logging.warning(mesg, label)


def find_misparsed_node(section_node, label, change, amended_labels):
    """ Nodes can get misparsed in the sense that we don't always know where
    they are in the tree. This uses label to find a candidate for a mis-parsed
    node and creates an appropriate change. """

    candidates = find_candidate(section_node, label[-1], amended_labels)
    if len(candidates) == 1:
        candidate = candidates[0]
        change['node'] = candidate
        change['candidate'] = True
        return change


def match_labels_and_changes(amendments, section_node):
    """ Given the list of amendments, and the parsed section node, match the
    two so that we're only changing what's been flagged as changing. This helps
    eliminate paragraphs that are just stars for positioning, for example.  """
    amended_labels = [a.label_id() for a in amendments]

    amend_map = defaultdict(list)
    for amend in amendments:
        change = {'action': amend.action}
        if amend.field is not None:
            change['field'] = amend.field

        if amend.action == 'MOVE':
            change['destination'] = amend.destination
            amend_map[amend.label_id()].append(change)
        elif amend.action == 'DELETE':
            amend_map[amend.label_id()].append(change)
        else:
            node = struct.find(section_node, amend.label_id())
            if node is None:
                candidate = find_misparsed_node(
                    section_node, amend.label, change, amended_labels)
                if candidate:
                    amend_map[amend.label_id()].append(candidate)
            else:
                change['node'] = node
                change['candidate'] = False
                amend_map[amend.label_id()].append(change)

    resolve_candidates(amend_map)
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


def create_reserve_amendment(amendment):
    """ Create a RESERVE related amendment. """
    return format_node(amendment['node'], amendment)


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

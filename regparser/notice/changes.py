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


def fix_label(label):
    """ The labels that come back from parsing the list of amendments have
    question marks (for the subpart) and other markers. Remove those here. """
    return [remove_intro(l) for l in label.split('-') if l != '?']


def fix_labels(labels_amended):
    """ The labels that come back from parsing the list of amendments need
    fixing so that we can use them. We do this en-mass here. """
    fixed = []
    for action, label in labels_amended:
        if isinstance(label, basestring):
            actual_label = fix_label(label)
            actual_label_id = '-'.join(actual_label)
            fixed.append((action, actual_label, actual_label_id))
        else:
            fixed_labels = [fix_label(l) for l in label]
            fixed_ids = ['-'.join(l) for l in fixed_labels]
            fixed.append((action, fixed_labels, fixed_ids))
    return fixed


def resolve_candidates(amend_map):
    """Ensure candidate isn't actually accounted for elsewhere, and fix
    it's label. """
    for label, node in amend_map.items():
        if 'node' in node:
            node_label = node['node'].label_id()
            if node['candidate'] and node_label not in amend_map:
                node['node'].label = label.split('-')


def match_labels_and_changes(labels_amended, section_node):
    amend_map = {}
    for action, label, label_id in labels_amended:
        if action == 'MOVE':
            amend_map[label_id[0]] = {
                'action': 'move', 'destination': label[1]}
        elif action == 'DELETE':
            amend_map[label_id] = {'action': 'deleted'}
        else:
            node = struct.find(section_node, label_id)
            if node is None:
                candidates = find_candidate(section_node, label[-1])
                if len(candidates) == 1:
                    candidate = candidates[0]
                    amend_map[label_id] = {
                        'action': 'updated',
                        'node': candidate,
                        'candidate': True}
            else:
                amend_map[label_id] = {
                    'node': node,
                    'action': 'updated',
                    'candidate': False}

    resolve_candidates(amend_map)
    return amend_map


def create_add_amendment(node):
    """ Create the JSON representation for a node that has been added for
    changed. The way notices are written we don't need to distinguish between
    nodes that have been added and those that have been updated. """

    nodes_list = []
    flatten_tree(nodes_list, node)

    def format_node(node):
        d = node_to_dict(n)
        d['op'] = 'updated'
        return {node.label_id(): d}

    nodes = [format_node(n) for n in nodes_list]
    return nodes


def flatten_tree(node_list, node):
    """ Flatten a tree, removing all hierarchical information, making a
    list out of all the nodes. """
    for c in node.children:
        flatten_tree(node_list, c)

    node.children = []
    node_list.append(node)


def remove_intro(l):
    """ Remove the marker that indicates this is a change to introductory
    text. """
    return l.replace('[text]', '')

import copy
from regparser.tree.struct import Node

""" Notices indicate how a regulation has changed since the last version. This
module contains code to compile a regulation from a notice's changes. """

class RegulationTree(object):
    def __init__(self, previous_tree):
        self.tree = copy.deepcopy(previous_tree)

    def replace_node_and_subtree(self, node):
        """ Replace the whole node with the one in change. """
        #find parent of node
        parent_label = node.label[:-1]

        #remove node from children list

        #add node to list

        #sort children


def dict_to_node(node_dict):
    """ Convert a dictionary representation of a node into a Node object if 
    it contains the minimum required field. Otherwise, pass it through 
    unchanged. """
    minimum_fields = set(('text', 'label', 'node_type'))
    if minimum_fields.issubset(node_dict.keys()):
        node = Node(
            node_dict['text'], [], node_dict['label'],
            node_dict.get('title', None), node_dict['node_type'])
        if 'tagged_text' in node_dict:
            node.tagged_text = node_dict['tagged_text']
        return node
    else:
        return node_dict

def compile_regulation(previous_tree, notice_changes):
    reg = RegulationTree(previous_tree)

    labels = sorted(notice_changes.keys(), key=lambda x: len(x[0]))

    for label in labels:
        changes = notice_changes[label]
        for change in changes:
            replace_subtree = 'field' not in change

            if change['action'] == 'PUT' and replace_subtree:
                node = dict_to_node(change['node'])
                reg.replace_node_and_subtree(node)

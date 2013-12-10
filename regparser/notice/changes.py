from regparser.tree import struct
from regparser.diff.treediff import node_to_dict

def find_candidate(root, label_last):
    def check(node):
        if node.label[-1] == label_last and node.children == []:
            return node
    response = struct.walk(root, check)
    return response

def match_labels_and_changes(labels_amended, section_node):
    amend_map = {}
    for action, label in labels_amended:
        if action == 'MOVE':
            pass
        elif action == 'DELETE':
            actual_label = fix_label(label)
            actual_label_id = '-'.join(actual_label)
            amend_map[actual_label_id] = {'action':'deleted'}
        elif '[text]' in label:
            pass
        else:
            actual_label = fix_label(label)
            actual_label_id = '-'.join(actual_label)
            node = struct.find(section_node, actual_label_id)
            if node is None:
                candidates = find_candidate(section_node, actual_label[-1])
                if len(candidates) == 1:
                    candidate = candidates[0]
                    amend_map[actual_label_id] = {
                        'action':'updated',
                        'node':candidate,
                        'candidate': True}
            else:
                amend_map[actual_label_id] = {
                    'node':node, 
                    'action': 'updated',
                    'candidate':False} 

    #Ensure candidate isn't actually accounted for elsewhere, and fix 
    #it's label. 
    for label, node in amend_map.items():
        if 'node' in node:
            node_label = node['node'].label_id()
            if node['candidate'] and node_label not in amend_map:
                node['node'].label = label.split('-')
    return amend_map

def create_add_amendment(node):
    nodes_list = []
    split_children(nodes_list, node)

    def format_node(node):
        d = node_to_dict(n)
        d['op'] = 'updated'
        return {node.label_id():d}

    nodes = [format_node(n) for n in nodes_list]
    return nodes

def split_children(node_list, node):
    for c in node.children:
        split_children(node_list, c)

    node.children = []
    node_list.append(node)

def remove_intro(l):
    """ Remove the marker that indicates this is a change to introductory
    text. """
    return l.replace('[text]', '')

def fix_label(label):
    label = [remove_intro(l) for l in label.split('-') if l != '?']
    return label



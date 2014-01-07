import copy
from regparser.tree.struct import Node, find
from regparser.utils import roman_nums

""" Notices indicate how a regulation has changed since the last version. This
module contains code to compile a regulation from a notice's changes. """

class RegulationTree(object):
    def __init__(self, previous_tree):
        self.tree = copy.deepcopy(previous_tree)

    def get_parent_label(self, node):
        parent_label = node.label[:-1]
        return '-'.join(parent_label)

    def make_label_sortable(self, label, roman=False):
        """ Make labels sortable, but converting them as appropriate. 
        Also, appendices have labels that look like 30(a), we make those 
        appropriately sortable. """

        if label.isdigit():
            return (int(label),)
        if label.isalpha():
            if roman:
                romans = list(itertools.islice(roman_nums(), 0, 50))
                return 1 + romans.index(label)
            else:
                return (label,)
        else:
            m = re.match(r"([0-9]+)([\(])([a-z]+)([\)])", label, re.I)
            return (int(m.groups()[0]), m.groups()[2])

    def add_child(self, children, node):
        children.append(node)

        for c in children:
            c.sortable = self.make_label_sortable(
                c.label[-1], roman=(len(c.label) == 5))

        children.sort(key=lambda x: x.sortable)
        return children

    def replace_node_and_subtree(self, node):
        """ Replace an existing node in the tree with node.  """
        #find parent of node
        parent_label = self.get_parent_label(node)
        parent = find(self.tree, parent_label) 

        other_children = [c for c in parent.children if c.label != node.label]
        parent.children = self.add_child(other_children, node)

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
            else:
                print label
    return reg

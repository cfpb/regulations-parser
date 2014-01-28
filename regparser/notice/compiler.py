""" Notices indicate how a regulation has changed since the last version. This
module contains code to compile a regulation from a notice's changes. """

import copy
import itertools
import re
import logging
from regparser.tree.struct import Node, find
from regparser.utils import roman_nums


def get_parent_label(node):
    """ Given a node, get the label of it's parent. """
    if node.node_type == Node.SUBPART:
        return node.label[0]
    elif node.node_type == Node.INTERP:
        marker_position = node.label.index(Node.INTERP_MARK)
        interpreting = node.label[:marker_position]
        comment_pars = node.label[marker_position + 1:]
        if comment_pars:                # 111-3-a-Interp-4-i
            return '-'.join(node.label[:-1])
        elif len(interpreting) > 1:     # 111-3-a-Interp
            return '-'.join(interpreting[:-1] + [Node.INTERP_MARK])
        else:                           # 111-Interp
            return node.label[0]
    else:
        parent_label = node.label[:-1]
        return '-'.join(parent_label)


_label_regex = re.compile(r"([0-9]+)([\(])([a-z]+)([\)])", re.I)


def make_label_sortable(label, roman=False):
    """ Make labels sortable, but converting them as appropriate.
    Also, appendices have labels that look like 30(a), we make those
    appropriately sortable. """

    if label.isdigit():
        return (int(label),)
    match = _label_regex.match(label)
    if match:
        return (int(match.groups()[0]), match.groups()[2])
    if roman:
        romans = list(itertools.islice(roman_nums(), 0, 50))
        return 1 + romans.index(label)
    else:
        return (label,)


def make_root_sortable(label, node_type):
    """ Child nodes of the root contain nodes of various types, these
    need to be sorted correctly. This returns a tuple to help
    sort these first level nodes. """

    if node_type == Node.SUBPART or node_type == Node.EMPTYPART:
        return (0, label[-1])
    elif node_type == Node.APPENDIX:
        return (1, label[-1])
    elif node_type == Node.INTERP:
        return (2,)


def replace_first_sentence(text, replacement):
    """ Replace the first sentence in text with replacement. This makes
    some incredibly simplifying assumptions - so buyer beware. """
    no_periods_replacement = replacement.replace('.', '')

    sentences = text.split('.', 1)
    if len(sentences) > 1:
        sentences[0] = no_periods_replacement
        return '.'.join(sentences)
    else:
        return replacement


class RegulationTree(object):
    """ This encapsulates a regulation tree, and methods to change that tree.
    """

    def __init__(self, previous_tree):
        self.tree = copy.deepcopy(previous_tree)

    def get_parent(self, node):
        """ Get the parent of a node. Returns None if parent not found. """
        parent_label_id = get_parent_label(node)
        return find(self.tree, parent_label_id)

    def add_to_root(self, node):
        """ Add a child to the root of the tree. """
        self.tree.children.append(node)

        for c in self.tree.children:
            c.sortable = make_root_sortable(c.label, c.node_type)

        self.tree.children.sort(key=lambda x: x.sortable)

        for c in self.tree.children:
            del c.sortable

    def add_child(self, children, node):
        """ Add a child to the children, and sort appropriately. This is used
        for non-root nodes. """

        children.append(node)

        for c in children:
            if c.label[-1] == Node.INTERP_MARK:
                c.sortable = make_label_sortable(
                    c.label[-2], roman=(len(c.label) == 6))
            elif Node.INTERP_MARK in c.label:
                marker_idx = c.label.index(Node.INTERP_MARK)
                comment_pars = c.label[marker_idx + 1:]
                c.sortable = make_label_sortable(
                    comment_pars[-1], roman=(len(comment_pars) == 2))
            else:
                c.sortable = make_label_sortable(
                    c.label[-1], roman=(len(c.label) == 5))

        children.sort(key=lambda x: x.sortable)

        for c in children:
            del c.sortable
        return children

    def delete_from_parent(self, node):
        """ Delete node from it's parent, effectively removing it from the
        tree. """

        parent = self.get_parent(node)
        other_children = [c for c in parent.children if c.label != node.label]
        parent.children = other_children

    def delete(self, label_id):
        """ Delete the node with label_id from the tree. """
        node = find(self.tree, label_id)
        self.delete_from_parent(node)

    def reserve(self, label_id, node):
        """ Reserve either an existing node (by replacing it) or
        reserve by adding a new node. When a node is reserved, it's
        represented in the FR XML. We simply use that represenation here
        instead of doing something else. """

        existing_node = find(self.tree, label_id)
        if existing_node is None:
            self.add_node(node)
        else:
            self.replace_node_and_subtree(node)

    def move(self, origin, destination):
        """ Move a node from one part in the tree to another. """
        origin = find(self.tree, origin)
        self.delete_from_parent(origin)

        #XXX  We'll need to fix the paragraph marker, but let's save that
        #for later
        origin.label = destination
        self.add_node(origin)

    def replace_node_and_subtree(self, node):
        """ Replace an existing node in the tree with node.  """
        parent = self.get_parent(node)
        other_children = [c for c in parent.children if c.label != node.label]
        parent.children = self.add_child(other_children, node)

    def create_empty_node(self, node_label):
        """ In rare cases, we need to flush out the tree by adding
        an empty node. """
        node_label = node_label.split('-')
        node = Node('', [], node_label, None, Node.REGTEXT)
        parent = self.get_parent(node)
        parent.children = self.add_child(parent.children, node)
        return parent

    def add_node(self, node):
        """ Add an entirely new node to the regulation tree. """

        if node.node_type == Node.SUBPART:
            return self.add_to_root(node)

        parent = self.get_parent(node)
        if parent is None:
            # This is a corner case, where we're trying to add a child
            # to a parent that should exist.
            logging.warning('No existing parent for: %s' % node.label_id())
            parent = self.create_empty_node(get_parent_label(node))
        parent.children = self.add_child(parent.children, node)

    def add_section(self, node, subpart_label):
        """ Add a new section to a subpart. """

        subpart = find(self.tree, '-'.join(subpart_label))
        subpart.children = self.add_child(subpart.children, node)

    def replace_node_text(self, label, change):
        """ Replace just a node's text. """

        node = find(self.tree, label)
        node.text = change['node']['text']

    def replace_node_title(self, label, change):
        """ Replace just a node's title. """

        node = find(self.tree, label)
        node.title = change['node']['title']

    def replace_node_heading(self, label, change):
        """ A node's heading is it's keyterm. We handle this here, but not
        well, I think. """
        node = find(self.tree, label)
        node.text = replace_first_sentence(node.text, change['node']['text'])

        if hasattr(node, 'tagged_text') and 'tagged_text' in change['node']:
            node.tagged_text = replace_first_sentence(
                node.tagged_text, change['node']['tagged_text'])

    def get_subparts(self):
        """ Get all the subparts and empty parts in the tree.  """

        def subpart_type(c):
            """ Return True if a subpart or an empty part. """
            return c.node_type in (Node.EMPTYPART, Node.SUBPART)

        return [c for c in self.tree.children if subpart_type(c)]

    def create_new_subpart(self, subpart_label):
        """ Create a whole new subpart. """

        #XXX Subparts need titles. We'll need to pull this up from parsing.
        subpart_node = Node('', [], subpart_label, None, Node.SUBPART)
        self.add_to_root(subpart_node)
        return subpart_node

    def get_subpart_for_node(self, label):
        """ Return the subpart a node resides in. Note that this can't be
        determined by simply looking at a node's label. """

        subparts = self.get_subparts()
        subparts_with_label = [s for s in subparts
                               if find(s, label) is not None]

        if len(subparts_with_label) > 0:
            return subparts_with_label[0]

    def move_to_subpart(self, label, subpart_label):
        """ Move an existing node to another subpart. If the new subpart
        doesn't exist, create it. """

        destination = find(self.tree, '-'.join(subpart_label))

        if destination is None:
            destination = self.create_new_subpart(subpart_label)

        subpart_with_node = self.get_subpart_for_node(label)

        if destination and subpart_with_node:
            node = find(subpart_with_node, label)
            other_children = [c for c in subpart_with_node.children
                              if c.label_id() != label]
            subpart_with_node.children = other_children
            destination.children = self.add_child(destination.children, node)


def dict_to_node(node_dict):
    """ Convert a dictionary representation of a node into a Node object if
    it contains the minimum required fields. Otherwise, pass it through
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


def sort_labels(labels):
    """ Deal with higher up elements first. """
    sorted_labels = sorted(labels, key=lambda x: len(x))

    #The length of a Subpart label doesn't indicate it's level in the tree
    subparts = [l for l in sorted_labels if 'Subpart' in l]
    non_subparts = [l for l in sorted_labels if 'Subpart' not in l]

    return subparts + non_subparts


def replace_node_field(reg, label, change):
    """ Call one of the field appropriate methods if we're changing just
    a field on a node. """

    if change['action'] == 'PUT' and change['field'] == '[text]':
        reg.replace_node_text(label, change)
    elif change['action'] == 'PUT' and change['field'] == '[title]':
        reg.replace_node_title(label, change)
    elif change['action'] == 'PUT' and change['field'] == '[heading]':
        reg.replace_node_heading(label, change)


def compile_regulation(previous_tree, notice_changes):
    """ Given a last full regulation tree, and the set of changes from the
    next final notice, construct the next full regulation tree. """
    reg = RegulationTree(previous_tree)
    labels = sort_labels(notice_changes.keys())
    field_list = ['[text]', '[title]', '[heading]']

    for label in labels:
        changes = notice_changes[label]
        for change in changes:
            replace_subtree = 'field' not in change

            if change['action'] == 'PUT' and replace_subtree:
                node = dict_to_node(change['node'])
                reg.replace_node_and_subtree(node)
            elif change['action'] == 'PUT' and change['field'] in field_list:
                replace_node_field(reg, label, change)
            elif change['action'] == 'POST':
                node = dict_to_node(change['node'])
                if 'subpart' in change and len(node.label) == 2:
                    reg.add_section(node, change['subpart'])
                else:
                    reg.add_node(node)
            elif change['action'] == 'DESIGNATE':
                if 'Subpart' in change['destination']:
                    reg.move_to_subpart(label, change['destination'])
            elif change['action'] == 'MOVE':
                reg.move(label, change['destination'])
            elif change['action'] == 'DELETE':
                reg.delete(label)
            elif change['action'] == 'RESERVE':
                node = dict_to_node(change['node'])
                reg.reserve(label, node)
            else:
                print "%s: %s" % (change['action'], label)
    return reg.tree

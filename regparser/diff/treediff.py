import difflib
import json
from regparser.tree import struct

INSERT = 'insert'
DELETE = 'delete'
REPLACE = 'replace'
EQUAL = 'equal'

def hash_nodes(reg_tree):
    """ Create a hash map to the nodes of a regulation tree.  """
    tree_hash = {}

    def per_node(node):
        tree_hash[node.label_id()] = node

    struct.walk(reg_tree, per_node)
    return tree_hash

def convert_insert(ins_op, new_text):
    """ The insert operation returned by difflib assumes we have access to both
    texts. We re-write the op, so that we don't make the same assumption. """
    return (INSERT, ins_op[1], new_text[ins_op[3]:ins_op[4]])

def convert_opcode(op, new_text):
    """ We want to express changes as inserts and deletes only. """
    code = op[0]
    if code == INSERT:
        return convert_insert(op, new_text)
    elif code == DELETE:
        return op
    elif code == REPLACE:
        del_op = (DELETE, op[1], op[2])
        add_op = convert_insert(
            (INSERT, op[1], op[1], op[3], op[4]), new_text)
        return [del_op, add_op]
  
def get_opcodes(old_text, new_text):
    seqm = difflib.SequenceMatcher(
        lambda x: x in " \t\n", 
        old_text, 
        new_text)
    opcodes = [convert_opcode(op, new_text) for op in seqm.get_opcodes() if op[0] != EQUAL]
    return opcodes

class Compare(object):
    def __init__(self, older, newer):
        self.older = older
        self.newer = newer
        self.newer_tree_hash = hash_nodes(newer)
        self.older_tree_hash = hash_nodes(older)

        self.changes = {}

    def add_title_opcodes(self, label, opcodes):
        if opcodes:
            if label in self.changes:
                self.changes[label]["title"] = opcodes
            else:
                self.changes[label] = {"op":"modified", "title":opcodes}

    def add_text_opcodes(self, label, opcodes):
        if opcodes:
            if label in self.changes:
                self.changes[label]["text"] = opcodes
            else:
                self.changes[label] = {"op":"modified", "text":opcodes}
                
    def deleted_and_modified(self, node):
        older_label = node.label_id()

        if older_label not in self.newer_tree_hash:
            self.changes[older_label] = {"op":"deleted"}
        else:
            newer_node = self.newer_tree_hash[older_label]
            text_opcodes = get_opcodes(node.text, newer_node.text)
            self.add_text_opcodes(older_label, text_opcodes)

            if node.title:
                title_opcodes = get_opcodes(node.title, newer_node.title)
                self.add_title_opcodes(older_label, title_opcodes)

    def added(self):
        """ The newer regulation likely has paragraphs, sections that are
        added. We identify those here, and add each node individually, without
        it's children. """

        for label in self.newer_tree_hash:
            if label not in self.older_tree_hash:
                node = self.newer_tree_hash[label]
                node.children = []
                self.changes[label] = {"op":"added", "node":node}

    def compare(self):
        struct.walk(self.older, self.deleted_and_modified)
        self.added()

    def write(self):
        """ Write out the changes. """
        print struct.NodeEncoder().encode(self.changes)
        

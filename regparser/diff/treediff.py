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

def convert_opcode(op):
    """ We want to express changes as inserts and deletes only. """
    code = op[0]
    if code == INSERT  or code == DELETE:
        return op
    elif code == REPLACE:
        del_op = (DELETE, op[1], op[2])
        add_op = (INSERT, op[1], op[1], op[3], op[4])
        return [del_op, add_op]
  
def get_opcodes(old_text, new_text):
    seqm = difflib.SequenceMatcher(
        lambda x: x in " \t\n", 
        old_text, 
        new_text)
    opcodes = [convert_opcode(op) for op in seqm.get_opcodes() if op[0] != EQUAL]
    return opcodes

def compare(older, newer):
    """ Compare the two regulation trees, generate the diff structure. """

    newer_tree_hash = hash_nodes(newer)
    deleted_sections = []

    changes = {}

    def per_node(node):
        older_label = node.label_id()

        if older_label not in newer_tree_hash:
            deleted_sections.append(older_label)
            changes[older_label] = {"op":"deleted"}
        else:
            newer_node = newer_tree_hash[older_label]

            text_opcodes = get_opcodes(node.text, newer_node.text)

            if text_opcodes:
                changes[older_label] = {"op":"modified", "text":text_opcodes}
            if node.title:
                title_opcodes = get_opcodes(node.title, newer_node.title)
                if title_opcodes:
                    if older_label in changes:
                        changes[older_label]['title'] = title_opcodes 
                    else:
                        changes[older_label] = {"op":"modified", "title":title_opcodes}
                        
    struct.walk(older, lambda n: per_node(n))
    print json.dumps(changes)

import difflib
import re

from regparser.layer.graphics import Graphics
from regparser.tree import struct


INSERT = 'insert'
DELETE = 'delete'
REPLACE = 'replace'
EQUAL = 'equal'


# Operations on nodes   - @todo: combine with above
ADDED = 'added'
MODIFIED = 'modified'
DELETED = 'deleted'


def deconstruct_text(text):
    """ Split the text into a list of words, but avoid graphics markers """
    excludes = [(m.start(), m.end()) for m in Graphics.gid.finditer(text)]
    spaces = [(m.start(), m.end()) for m in re.finditer(r'\s+', text)]
    spaces = [(s[0], s[1]) for s in spaces
              if not any(e[0] <= s[0] and e[1] >= s[1] for e in excludes)]

    last_space, words = 0, []
    for s in spaces:
        words.append(text[last_space:s[0]])
        # Also add the space as a word
        words.append(text[s[0]:s[1]])
        # Update position
        last_space = s[1]
    # Add the last bit of text (unless we've already grabbed it)
    if last_space != len(text):
        words.append(text[last_space:])

    return words


def reconstruct_text(text_list):
    """ We split the text into a list of words, reconstruct that
    text back from the list. """
    return ''.join(text_list)


def convert_insert(ins_op, old_text_list, new_text_list):
    """ The insert operation returned by difflib assumes we have access to both
    texts. We re-write the op, so that we don't make the same assumption. """

    char_offset_start = len(reconstruct_text(old_text_list[0:ins_op[1]]))
    return (
        INSERT,
        char_offset_start,
        reconstruct_text(new_text_list[ins_op[3]:ins_op[4]]))


def convert_delete(op, old_text_list):
    """ Convert the delete opcode from a word based offset, to a character
    based offset. """

    opcode, s, e = op
    prefix = reconstruct_text(old_text_list[0:s])
    prefix_length = len(prefix)
    text = reconstruct_text(old_text_list[s:e])
    text_length = len(text)

    char_offset_start = prefix_length
    char_offset_end = prefix_length + text_length

    return (opcode, char_offset_start, char_offset_end)


def convert_opcode(op, new_text_list, old_text_list):
    """ We want to express changes as inserts and deletes only. """
    code = op[0]
    if code == INSERT:
        return convert_insert(op, old_text_list, new_text_list)
    elif code == DELETE:
        # Deletes have an extra set of co-ordinates which
        # we don't need.
        return convert_delete((DELETE, op[1], op[2]), old_text_list)
    elif code == REPLACE:
        del_op = convert_delete((DELETE, op[1], op[2]), old_text_list)
        add_op = convert_insert(
            (INSERT, op[1], op[1], op[3], op[4]), old_text_list, new_text_list)
        return [del_op, add_op]


def get_opcodes(old_text, new_text):
    """ Get the operation codes that convert old_text into
    new_text. """

    old_word_list = deconstruct_text(old_text)
    new_word_list = deconstruct_text(new_text)

    seqm = difflib.SequenceMatcher(
        lambda x: x in " \t\n",
        old_word_list,
        new_word_list)

    opcodes = [
        convert_opcode(op, new_word_list, old_word_list)
        for op in seqm.get_opcodes() if op[0] != EQUAL]
    return opcodes


def _local_changes(lhs, rhs):
    """Account for only text changes between nodes. This explicitly excludes
    children"""
    if lhs.text == rhs.text and lhs.title == rhs.title:
        return []
    else:
        node_changes = {"op": MODIFIED}

        text_opcodes = get_opcodes(lhs.text, rhs.text)
        if text_opcodes:
            node_changes["text"] = text_opcodes

        title_opcodes = get_opcodes(lhs.title, rhs.title)
        if title_opcodes:
            node_changes["title"] = title_opcodes
        return [(lhs.label_id, node_changes)]


def _new_in_rhs(lhs_list, rhs_list):
    """Compare the lhs and rhs lists to see if the rhs contains elements not
    in the lhs"""
    added = []
    lhs_codes = tuple(map(lambda n: n.label_id, lhs_list))
    for node in rhs_list:
        if node.label_id not in lhs_codes:
            added.append(node)
    return added


def _index_by_label_id(nodes):
    # Replace with dict comprehension when not on 2.6
    return dict((n.label_id, n) for n in nodes)


def _data_for_add(node):
    node_as_dict = {
        'child_labels': tuple(c.label_id for c in node.children),
        'label': node.label,
        'node_type': node.node_type,
        'tagged_text': node.tagged_text or None,  # maintain backwards compat
        'text': node.text,
        'title': node.title or None,
    }
    return (node.label_id, {"op": ADDED, "node": node_as_dict})


def _data_for_delete(node):
    return (node.label_id, {"op": DELETED})


def changes_between(lhs, rhs):
    """Main entry point for this library. Recursively return a list of changes
    between the lhs and rhs. lhs and rhs should be FrozenNodes. Note that this
    *does not* account for reordering nodes, though it does account for
    limited moves (e.g. when renaming subparts)."""
    changes = []
    if lhs == rhs:
        return changes

    changes.extend(_local_changes(lhs, rhs))

    # Removed children. Note params reversed
    removed_children = _new_in_rhs(rhs.children, lhs.children)
    changes.extend(map(_data_for_delete, removed_children))
    # grandchildren which appear to be deleted, but may just have been moved
    possibly_moved = _index_by_label_id(
        grandchild
        for child in removed_children for grandchild in child.children)

    # New children. Determine if they are added or moved
    for added in _new_in_rhs(lhs.children, rhs.children):
        changes.append(_data_for_add(added))
        for grandchild in added.children:
            if grandchild.label_id in possibly_moved:   # it *was* moved
                changes.extend(changes_between(
                    possibly_moved[grandchild.label_id], grandchild))
                del possibly_moved[grandchild.label_id]
            else:   # Not moved; recursively add all of it's children
                changes.extend(struct.walk(grandchild, _data_for_add))

    # Remaining nodes weren't moved; they were *re*moved
    for removed in possibly_moved.values():
        changes.extend(struct.walk(removed, _data_for_delete))

    # Recurse on modified children. Again, this does *not* track reordering
    for lhs_child in lhs.children:
        for rhs_child in rhs.children:
            if lhs_child.label_id == rhs_child.label_id:
                changes.extend(changes_between(lhs_child, rhs_child))
    return changes

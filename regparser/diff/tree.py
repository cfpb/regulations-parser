from regparser.diff.text import get_opcodes
from regparser.tree import struct


ADDED = 'added'
MODIFIED = 'modified'
DELETED = 'deleted'


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
    possibly_moved = {}
    for child in removed_children:
        for grandchild in child.children:
            possibly_moved[grandchild.label_id] = grandchild

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

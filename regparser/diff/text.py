import difflib
import re

from regparser.layer.graphics import Graphics


INSERT = 'insert'
DELETE = 'delete'
REPLACE = 'replace'
EQUAL = 'equal'


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

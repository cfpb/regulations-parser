import re


def find_start(text, heading, index):
    """Find the start of an appendix, supplement, etc."""
    match = re.search(r'^%s %s' % (heading, index), text, re.MULTILINE)
    if match:
        return match.start()


def find_offsets(text, search_fn):
    """Find the start and end of an appendix, supplement, etc."""
    start = search_fn(text)
    if start is None or start == -1:
        return None

    post_start_text = text[start+1:]
    end = search_fn(post_start_text)
    if end and end > -1:
        return (start, start + end + 1)
    else:
        return (start, len(text))


def segments(text, offsets_fn, exclude=[]):
    """Split a block of text into a list of its sub parts. Often this means
    calling the offsets function repeatedly until there is no more text to
    process."""
    segs = []
    seg_id = 0
    remaining_text = text
    text_offset = 0
    offsets = offsets_fn(remaining_text, seg_id, exclude)
    while offsets:
        begin, end = offsets
        segs.append((begin+text_offset, end+text_offset))
        seg_id += 1
        text_offset += end

        remaining_text = remaining_text[end:]
        exclude = [(e[0]-end, e[1]-end) for e in exclude]
        offsets = offsets_fn(remaining_text, seg_id, exclude)
    return segs

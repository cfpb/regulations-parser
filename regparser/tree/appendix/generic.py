from regparser import search


def is_title_case(line):
    """Determine if a line is title-case (i.e. the first letter of every
    word is upper-case. More readable than the equivalent all([]) form."""
    for word in line.split(u' '):
        if len(word) > 0 and len(word) > 3 and word[0] != word[0].upper():
            return False
    return True


def find_next_segment(text):
    """Find the start/end of the next segment. A segment for the generic
    appendix parser is something separated by a title-ish line (a short line
    with title-case words)."""
    lines = text.split("\n")
    for i in range(len(lines) - 1):
        lines[i] = lines[i] + "\n"
    start = 0
    end = 0
    found_start = False
    for line in lines + ["Placeholder Title"]:
        if len(line.strip()) > 0 and len(line) < 100 and is_title_case(line):
            if found_start:
                return (start, end)
            else:
                found_start = True
        end += len(line)
        if not found_start:
            start += len(line)


def segments(text):
    """Return a list of segment offsets. See find_next_segment()"""
    def offsets_fn(remaining_text, idx, excludes):
        return find_next_segment(remaining_text)
    return search.segments(text, offsets_fn)

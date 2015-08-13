import itertools
import re
import string

from regparser.tree import struct
from regparser.search import segments
from regparser.utils import roman_nums

p_levels = [
    list(string.ascii_lowercase),
    [str(i) for i in range(1, 51)],
    list(itertools.islice(roman_nums(), 0, 50)),
    list(string.ascii_uppercase),
    ['<E T="03">' + str(i) + '</E>' for i in range(1, 51)],
    ['<E T="03">' + i + '</E>'
     for i in itertools.islice(roman_nums(), 0, 50)]
]


def p_level_of(marker):
    """Given a marker(string), determine the possible paragraph levels it
    could fall into. This is useful for determining the order of
    paragraphs"""
    potential_levels = []
    for level, markers in enumerate(p_levels):
        if marker in markers:
            potential_levels.append(level)
    return potential_levels


class ParagraphParser():

    def __init__(self, p_regex, node_type):
        """p_regex is the regular expression used when searching through
        paragraphs. It should contain a %s for the next paragraph 'part'
        (e.g. 'a', 'A', '1', 'i', etc.) inner_label_fn is a function which
        takes the current label, and the next paragraph 'part' and produces
        a new label."""
        self.p_regex = p_regex
        self.node_type = node_type

    def matching_subparagraph_ids(self, p_level, paragraph):
        """Return a list of matches if this paragraph id matches one of the
        subparagraph ids (e.g.  letter (i) and roman numeral (i)."""
        matches = []
        for depth in range(p_level+1, len(p_levels)):
            for sub_id, sub in enumerate(p_levels[depth]):
                if sub == p_levels[p_level][paragraph]:
                    matches.append((depth, sub_id))
        return matches

    def best_start(self, text, p_level, paragraph, starts, exclude=[]):
        """Given a list of potential paragraph starts, pick the best based
        on knowledge of subparagraph structure. Do this by checking if the
        id following the subparagraph (e.g. ii) is between the first match
        and the second. If so, skip it, as that implies the first match was
        a subparagraph."""
        subparagraph_hazards = self.matching_subparagraph_ids(
            p_level, paragraph)
        starts = starts + [(len(text), len(text))]
        for i in range(1, len(starts)):
            _, prev_end = starts[i-1]
            next_start, _ = starts[i]
            s_text = text[prev_end:next_start]
            s_exclude = [
                (e_start + prev_end, e_end + prev_end)
                for e_start, e_end in exclude]
            is_subparagraph = False
            for hazard_level, hazard_idx in subparagraph_hazards:
                if self.find_paragraph_start_match(
                        s_text, hazard_level, hazard_idx + 1, s_exclude):
                    is_subparagraph = True
            if not is_subparagraph:
                return starts[i-1]

    def find_paragraph_start_match(self, text, p_level, paragraph, exclude=[]):
        """Find the positions for the start and end of the requested label.
        p_Level is one of 0,1,2,3; paragraph is the index within that label.
        Return None if not present. Does not return results in the exclude
        list (a list of start/stop indices). """
        if len(p_levels) <= p_level or len(p_levels[p_level]) <= paragraph:
            return None
        match_starts = [(m.start(), m.end()) for m in re.finditer(
            self.p_regex % p_levels[p_level][paragraph], text)]
        match_starts = [
            (start, end) for start, end in match_starts
            if all([end < es or start > ee for es, ee in exclude])]

        if len(match_starts) == 0:
            return None
        elif len(match_starts) == 1:
            return match_starts[0]
        else:
            return self.best_start(
                text, p_level, paragraph, match_starts, exclude)

    def paragraph_offsets(self, text, p_level, paragraph, exclude=[]):
        """Find the start/end of the requested paragraph. Assumes the text
        does not just up a p_level -- see build_paragraph_tree below."""
        start = self.find_paragraph_start_match(
            text, p_level, paragraph, exclude)
        if start is None:
            return None
        id_start, id_end = start
        end = self.find_paragraph_start_match(
            text[id_end:], p_level, paragraph + 1,
            [(e_start - id_end, e_end - id_end)
                for e_start, e_end in exclude])
        if end is None:
            end = len(text)
        else:
            end = end[0] + id_end
        return (id_start, end)

    def paragraphs(self, text, p_level, exclude=[]):
        """Return a list of paragraph offsets defined by the level param."""
        def offsets_fn(remaining_text, p_idx, exclude):
            return self.paragraph_offsets(
                remaining_text, p_level, p_idx, exclude)
        return segments(text, offsets_fn, exclude)

    def build_tree(self, text, p_level=0, exclude=[], label=[],
                   title=''):
        """
        Build a dict to represent the text hierarchy.
        """
        subparagraphs = self.paragraphs(text, p_level, exclude)
        if subparagraphs:
            body_text = text[0:subparagraphs[0][0]]
        else:
            body_text = text

        children = []
        for paragraph, (start, end) in enumerate(subparagraphs):
            new_text = text[start:end]
            new_excludes = [(e[0] - start, e[1] - start) for e in exclude]
            new_label = label + [p_levels[p_level][paragraph]]
            children.append(
                self.build_tree(
                    new_text, p_level + 1, new_excludes, new_label))
        return struct.Node(body_text, children, label, title, self.node_type)

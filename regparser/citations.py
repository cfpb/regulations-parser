from itertools import chain, takewhile

from regparser.grammar import unified as grammar
from regparser.tree.struct import Node


class Label(object):
    app_sect_schema = ('part', 'appendix', 'appendix_section', 'p1', 'p2',
                       'p3', 'p4', 'p5', 'p6')
    app_schema = ('part', 'appendix', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6')
    sect_schema = ('part', 'section', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6')

    comment_schema = ('comment', 'c1', 'c2', 'c3')

    @staticmethod
    def determine_schema(settings):
        if 'appendix_section' in settings:
            return Label.app_sect_schema
        elif 'appendix' in settings:
            return Label.app_schema
        else:
            return Label.sect_schema

    def __init__(self, schema = None, **kwargs):
        if schema is None:
            schema = Label.determine_schema(kwargs)
        self.settings = kwargs
        self.schema = schema
        self.comment = any(kwargs.get(field) for field in
                           Label.comment_schema)

    def copy(self, schema = None, **kwargs):
        """Keep any relevant prefix when copying"""
        kwschema = Label.determine_schema(kwargs)
        if schema is None and kwschema != Label.sect_schema:
            schema = kwschema
        elif schema is None:
            schema = self.schema

        new_settings = {}
        found_start = False
        for field in (schema + Label.comment_schema):
            if field in kwargs:
                found_start = True
                new_settings[field] = kwargs[field]
            if not found_start:
                new_settings[field] = self.settings.get(field)
        return Label(**new_settings)

    def to_list(self):
        lst = list(map(lambda f: self.settings.get(f), self.schema))
        if self.comment:
            lst.append(Node.INTERP_MARK)
            lst.append(self.settings.get('c1'))
            lst.append(self.settings.get('c2'))
            lst.append(self.settings.get('c3'))

        return filter(bool, lst)



class ParagraphCitation(object):
    def __init__(self, start, end, label, full_start = None, full_end = None):
        if full_start is None:
            full_start = start
        if full_end is None:
            full_end = end

        self.start, self.end, self.label = start, end, label
        self.full_start, self.full_end = full_start, full_end

    def __contains__(self, other):
        """Proper inclusion"""
        return (other.full_start >= self.full_start
                and other.full_end <= self.full_end
                and (other.full_end != self.full_end
                     or other.full_start != self.full_start))

    def __repr__(self):
        return "ParagraphCitation( start=%s, end=%s, label=%s )" % (
            repr(self.start), repr(self.end), repr(self.label))


def match_to_label(match, initial_label, comment=False):
    """Return the citation and offsets for this match"""
    if comment:
        field_map = {'comment': True}
    else:
        field_map = {}
    for field in ('part', 'section', 'appendix', 'appendix_section', 'p1',
                  'p2', 'p3', 'p4', 'p5', 'p6', 'c1', 'c2', 'c3'):
        value = getattr(match, field)
        if value:
            field_map[field] = value

    label = initial_label.copy(**field_map)
    return label


def internal_citations(text, initial_label):
    citations = []

    def multiple_citations(matches, comment):
        """i.e. head :: tail"""
        for match, start, end in matches:
            label = initial_label
            for submatch in chain([match.head], match.tail):
                cit = ParagraphCitation(
                    submatch.pos[0], submatch.pos[1],
                    match_to_label(submatch.tokens, label, comment=comment),
                    full_start=start,
                    full_end=end)
                label = cit.label   # update the label to keep context
                citations.append(cit)

    def single_citations(matches, comment):
        for match, start, end in matches:
            citations.append(ParagraphCitation(
                start, end, match_to_label(match, initial_label,
                                           comment=comment)))

    multiple_citations(grammar.marker_comments.scanString(text), True)
    single_citations(grammar.marker_comment.scanString(text), True)

    multiple_citations(grammar.marker_paragraphs.scanString(text), False)
    multiple_citations(grammar.mps_paragraphs.scanString(text), False)
    multiple_citations(grammar.marker_sections.scanString(text), False)
    multiple_citations(grammar.appendix_with_sections.scanString(text), False)

    single_citations(grammar.marker_appendix.scanString(text), False)
    single_citations(grammar.appendix_with_section.scanString(text), False)
    single_citations(grammar.marker_paragraph.scanString(text), False)
    single_citations(grammar.mps_paragraph.scanString(text), False)
    single_citations(grammar.section_paragraph.scanString(text), False)

    # Remove any sub-citations
    final_citations = []
    for cit in citations:
        if not any(cit in other for other in citations):
            final_citations.append(cit)

    return final_citations

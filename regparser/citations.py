from itertools import chain

from regparser.grammar import unified as grammar
from regparser.tree.struct import Node


class Label(object):
    #   @TODO: subparts
    app_sect_schema = ('part', 'appendix', 'appendix_section', 'p1', 'p2',
                       'p3', 'p4', 'p5', 'p6')
    app_schema = ('part', 'appendix', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6')
    sect_schema = ('part', 'section', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6')
    default_schema = sect_schema

    comment_schema = ('comment', 'c1', 'c2', 'c3', 'c4')

    @staticmethod
    def from_node(node):
        """Best guess for schema based on the provided
           regparser.tree.struct.Node"""
        if (node.node_type == Node.APPENDIX
            or (node.node_type == Node.INTERP
                and len(node.label) > 2
                and node.label[1].isalpha())):
            if len(node.label) > 2 and node.label[2].isdigit():
                schema = Label.app_sect_schema
            else:
                schema = Label.app_schema
        else:
            schema = Label.sect_schema

        settings = {'comment': node.node_type == Node.INTERP}
        for idx, value in enumerate(node.label):
            if value == 'Interp':
                #   Add remaining bits as comment fields
                for cidx in range(idx+1, len(node.label)):
                    comment_field = Label.comment_schema[cidx - idx]
                    settings[comment_field] = node.label[cidx]
                #   Stop processing the prefix fields
                break
            settings[schema[idx]] = value
        return Label(**settings)

    @staticmethod
    def determine_schema(settings):
        if 'appendix_section' in settings:
            return Label.app_sect_schema
        elif 'appendix' in settings:
            return Label.app_schema
        elif 'section' in settings:
            return Label.sect_schema

    def __init__(self, schema=None, **kwargs):
        self.using_default_schema = False
        if schema is None:
            schema = Label.determine_schema(kwargs)
        if schema is None:
            self.using_default_schema = True
            schema = Label.default_schema
        self.settings = kwargs
        self.schema = schema
        self.comment = any(kwargs.get(field) for field in
                           Label.comment_schema)

    def copy(self, schema=None, **kwargs):
        """Keep any relevant prefix when copying"""
        kwschema = Label.determine_schema(kwargs)
        set_schema = bool(schema or kwschema
                          or not self.using_default_schema)

        if schema is None:
            if kwschema:
                schema = kwschema
            else:
                schema = self.schema

        if set_schema:
            new_settings = {'schema': schema}
        else:
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

    def __repr__(self):
        return repr(self.to_list())

    def __eq__(self, other):
        """Equality if types match and fields match"""
        return (type(other) == type(self)
                and self.using_default_schema == other.using_default_schema
                and self.settings == other.settings
                and self.schema == other.schema
                and self.comment == other.comment)


class ParagraphCitation(object):
    def __init__(self, start, end, label, full_start=None, full_end=None,
                 in_clause=False):
        if full_start is None:
            full_start = start
        if full_end is None:
            full_end = end

        self.start, self.end, self.label = start, end, label
        self.full_start, self.full_end = full_start, full_end
        self.in_clause = in_clause

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
        value = getattr(match, field) or getattr(match, 'plaintext_' + field)
        if value:
            field_map[field] = value

    label = initial_label.copy(**field_map)
    return label


def internal_citations(text, initial_label=None,
                       require_marker=False, title=None):
    """List of all internal citations in the text. require_marker helps by
    requiring text be prepended by 'comment'/'paragraphs'/etc. title
    represents the CFR title (e.g. 11 for FEC, 12 for CFPB regs) and is used
    to correctly parse citations of the the form 11 CFR 110.1 when
    11 CFR 110 is the regulation being parsed."""
    if not initial_label:
        initial_label = Label()
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
                    full_end=end,
                    in_clause=True)
                label = cit.label   # update the label to keep context
                citations.append(cit)

    def single_citations(matches, comment):
        for match, start, end in matches:
            full_start = start
            if match.marker is not '':
                #   Remove the marker from the beginning of the string
                start = match.marker.pos[1]
            citations.append(ParagraphCitation(
                start, end, match_to_label(match, initial_label,
                                           comment=comment),
                full_start=full_start))

    single_citations(grammar.marker_comment.scanString(text), True)

    multiple_citations(grammar.multiple_non_comments.scanString(text), False)
    multiple_citations(grammar.multiple_appendix_section.scanString(text),
                       False)
    multiple_citations(grammar.multiple_comments.scanString(text), True)
    multiple_citations(grammar.multiple_appendices.scanString(text), False)
    multiple_citations(grammar.multiple_period_sections.scanString(text),
                       False)

    single_citations(grammar.marker_appendix.scanString(text), False)
    single_citations(grammar.appendix_with_section.scanString(text), False)
    single_citations(grammar.section_of_appendix_to_this_part.scanString(text),
                     False)
    single_citations(grammar.marker_paragraph.scanString(text), False)
    single_citations(grammar.mps_paragraph.scanString(text), False)
    single_citations(grammar.m_section_paragraph.scanString(text), False)
    if not require_marker:
        single_citations(grammar.section_paragraph.scanString(text), False)
        single_citations(grammar.part_section_paragraph.scanString(text),
                         False)
        multiple_citations(
            grammar.multiple_section_paragraphs.scanString(text), False)

    for gram in (grammar.appendix_with_part, grammar.appendix_par_of_part):
        for match, start, end in gram.scanString(text):
            full_start = start
            if match.marker is not '':
                start = match.marker.pos[1]
            label = filter(lambda l: l != '.', list(match)[1:])
            if match.appendix:
                extra = dict(zip(['p1', 'p2', 'p3'], label[2:]))
                citations.append(ParagraphCitation(
                    start, end, initial_label.copy(
                        appendix=match.appendix, appendix_section=match.a1,
                        **extra), full_start=full_start))
            else:
                extra = dict(zip(['p1', 'p2', 'p3'], label[:-1]))
                citations.append(ParagraphCitation(
                    start, end,
                    initial_label.copy(appendix_section=match.a1, **extra),
                    full_start=full_start))

    # Internal citations can sometimes be in the form XX CFR YY.ZZ
    for match, start, end in grammar.internal_cfr_p.scanString(text):
        # Check if this is a reference to the CFR title and part we are parsing
        if match.cfr_title == title and match[1] == initial_label.to_list()[0]:
            full_start = start
            if match.marker is not '':
                #   Remove the marker from the beginning of the string
                start = match.marker.pos[1]
            citations.append(ParagraphCitation(
                start, end, match_to_label(match, initial_label),
                full_start=full_start))
        else:
            continue

    # And sometimes there are several of them
    for match, start, end in grammar.multiple_cfr_p.scanString(text):
        label = initial_label
        if match.head.cfr_title == title:
            for submatch in chain([match.head], match.tail):
                if submatch.part == initial_label.to_list()[0]:
                    cit = ParagraphCitation(
                        submatch.pos[0], submatch.pos[1],
                        match_to_label(submatch.tokens, label),
                        full_start=start,
                        full_end=end,
                        in_clause=True)
                    label = cit.label   # update the label to keep context
                    citations.append(cit)
        else:
            continue

    # Remove any sub-citations
    final_citations = []
    for cit in citations:
        if not any(cit in other for other in citations):
            final_citations.append(cit)

    return final_citations


def remove_citation_overlaps(text, possible_markers):
    """Given a list of markers, remove any that overlap with citations"""
    return [(m, start, end) for m, start, end in possible_markers
            if not any((e.start <= start and e.end >= start)
                       or (e.start <= end and e.end >= end)
                       or (start <= e.start and end >= e.end)
                       for e in internal_citations(text))]

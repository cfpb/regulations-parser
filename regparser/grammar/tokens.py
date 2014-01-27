""" Set of Tokens to be used when parsing.
    @label is a list describing the depth of a paragraph/context. It follows:
    [ Part, Subpart/Appendix/Interpretations, Section, p-level-1, p-level-2,
    p-level-3, p-level4, p-level5 ]
"""


def _none_str(value):
    """Shorthand for displaying a variable as a string or the text None"""
    if value is None:
        return 'None'
    else:
        return "'%s'" % value


class Verb:
    """Represents what action is taking place to the paragraphs"""

    PUT = 'PUT'
    POST = 'POST'
    MOVE = 'MOVE'
    DELETE = 'DELETE'
    DESIGNATE = 'DESIGNATE'

    def __init__(self, verb, active):
        self.verb = verb
        self.active = active

    def __repr__(self):
        return "Verb( '%s', active=%s )" % (self.verb, self.active)

    def __eq__(self, other):
        return repr(self) == repr(other)


class Context:
    """Represents a bit of context for the paragraphs. This gets compressed
    with the paragraph tokens to define the full scope of a paragraph. To
    complicate matters, sometimes what looks like a Context is actually the
    entity which is being modified (i.e. a paragraph). If we are certain
    that this is only context, (e.g. "In Subpart A"), use 'certain'"""

    def __init__(self, label, certain=False):
        # replace with Nones
        self.label = [p or None for p in label]
        self.certain = certain

    def __repr__(self):
        return "Context([ %s , certain=%s ])" % (
            ', '.join(map(_none_str, self.label)), self.certain)

    def __eq__(self, other):
        return repr(self) == repr(other)


class Paragraph:
    """Represents an entity which is being modified by the amendment. Label
    is a way to locate this paragraph (though see the above note). We might
    be modifying a field of a paragraph (e.g. intro text only, or title
    only;) if so, set the `field` parameter."""

    TEXT_FIELD = 'text'
    HEADING_FIELD = 'title'

    def __init__(self, label, field=None):
        # replace with Nones
        self.label = [p or None for p in label]
        # Trim the right side of the list
        while self.label and not self.label[-1]:
            self.label.pop()
        self.field = field

    def __repr__(self):
        return "Paragraph([ %s ], field = %s )" % (
            ', '.join(map(_none_str, self.label)), _none_str(self.field))

    def label_text(self):
        """Converts self.label into a string"""
        label = [p or '?' for p in self.label]
        if self.field:
            return '-'.join(label) + '[%s]' % self.field
        else:
            return '-'.join(label)

    def __eq__(self, other):
        return repr(self) == repr(other)


class TokenList:
    """Represents a sequence of other tokens, e.g. comma separated of
    created via "through" """

    def __init__(self, tokens):
        self.tokens = tokens

    def __repr__(self):
        return "TokenList([ %s ])" % ', '.join(map(repr, self.tokens))

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __iter__(self):
        return iter(self.tokens)

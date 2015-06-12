""" Set of Tokens to be used when parsing.
    @label is a list describing the depth of a paragraph/context. It follows:
    [ Part, Subpart/Appendix/Interpretations, Section, p-level-1, p-level-2,
    p-level-3, p-level4, p-level5 ]
"""
from copy import copy


def _none_str(value):
    """Shorthand for displaying a variable as a string or the text None"""
    if value is None:
        return 'None'
    else:
        return "'%s'" % value


class Token(object):
    """Base class for all tokens. Provides methods for pattern matching and
    copying this token"""
    def match(self, *types, **fields):
        """Pattern match. self must be one of the types provided (if they
        were provided) and all of the fields must match (if fields were
        provided)"""
        return ((not types or any(isinstance(self, typ) for typ in types))
                and (not fields or all(hasattr(self, f) for f in fields))
                and (not fields or all(getattr(self, f) == v
                                       for f, v in fields.iteritems())))

    def copy(self, **fields):
        """Helper method to create a new instance of this token with the
        **fields set."""
        new_version = copy(self)
        for field, value in fields.iteritems():
            setattr(new_version, field, value)
        return new_version

    def __eq__(self, other):
        return isinstance(other, self.__class__) and repr(self) == repr(other)

    def __ne__(self, other):
        """Must always define inequality when defining equality in Python"""
        return not self == other


class Verb(Token):
    """Represents what action is taking place to the paragraphs"""

    PUT = 'PUT'
    POST = 'POST'
    MOVE = 'MOVE'
    DELETE = 'DELETE'
    DESIGNATE = 'DESIGNATE'
    RESERVE = 'RESERVE'
    KEEP = 'KEEP'

    def __init__(self, verb, active, and_prefix=False):
        self.verb = verb
        self.active = active
        self.and_prefix = and_prefix

    def __repr__(self):
        return "Verb( %s, active=%s, and_prefix=%s)" % (
            repr(self.verb), repr(self.active), repr(self.and_prefix))


class Context(Token):
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


class Paragraph(Token):
    """Represents an entity which is being modified by the amendment. Label
    is a way to locate this paragraph (though see the above note). We might
    be modifying a field of a paragraph (e.g. intro text only, or title
    only;) if so, set the `field` parameter."""

    TEXT_FIELD = 'text'
    HEADING_FIELD = 'title'
    KEYTERM_FIELD = 'heading'

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


class TokenList(Token):
    """Represents a sequence of other tokens, e.g. comma separated of
    created via "through" """

    def __init__(self, tokens):
        self.tokens = tokens

    def __repr__(self):
        return "TokenList([ %s ])" % ', '.join(map(repr, self.tokens))

    def __iter__(self):
        return iter(self.tokens)


class AndToken(Token):
    """The word 'and' can help us determine if a Context token should be a
    Paragraph token. Note that 'and' might also trigger the creation of a
    TokenList, which takes precedent"""

    def __repr__(self):
        return "AndToken()"

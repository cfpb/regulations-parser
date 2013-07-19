""" Set of Tokens to be used when parsing.
    @label is a list describing the depth of a paragraph/context. It follows:
        [ Part, Subpart/Appendix/Interpretations, Section, p-level-1,
        p-level-2, p-level-3, p-level4, p-level5]
"""

def _none_str(value):
    if value is None:
        return 'None'
    else:
        return "'%s'" % value


class Verb:
    PUT = 'PUT'
    POST = 'POST'
    MOVE = 'MOVE'
    DELETE = 'DELETE'

    def __init__(self, verb, active):
        self.verb = verb
        self.active = active
    def __repr__(self):
        return "Verb( '%s', active=%s )" % (self.verb, self.active)
    def __eq__(self, other):
        return repr(self) == repr(other)


class Context:
    def __init__(self, label, certain=False):
        self.label = label
        self.certain = certain
    def __repr__(self):
        return "Context([ %s , certain=%s ])" % (
            ', '.join(map(_none_str, self.label)), self.certain)
    def __eq__(self, other):
        return repr(self) == repr(other)


class Paragraph:
    def __init__(self, label, field=None):
        self.label = [p or None for p in label] #   replace with Nones
        #   Trim the right side of the list
        while self.label and not self.label[-1]:
            self.label.pop()
        self.field = field
    def __repr__(self):
        return "Paragraph([ %s ], field = %s )" % (
                ', '.join(map(_none_str, self.label)), _none_str(self.field))
    def label_text(self):
        label = [p or '?' for p in self.label]
        if self.field:
            return '-'.join(label) + '[%s]' % self.field
        else:
            return '-'.join(label)
    def __eq__(self, other):
        return repr(self) == repr(other)


class TokenList:
    def __init__(self, tokens):
        self.tokens = tokens
    def __repr__(self):
        return "TokenList([ %s ])" % ', '.join(map(repr, self.tokens))
    def __eq__(self, other):
        return repr(self) == repr(other)


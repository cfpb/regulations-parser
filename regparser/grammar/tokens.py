def _none_str(value):
    if value is None:
        return 'None'
    else:
        return "'%s'" % value


class Verb:
    def __init__(self, verb, active):
        self.verb = verb
        self.active = active
    def __repr__(self):
        return "Verb( '%s', active=%s )" % (self.verb, self.active)


class Context:
    def __init__(self, label, certain):
        self.label = label
        self.certain = certain
    def __repr__(self):
        return "Context([ %s , certain=%s ])" % (
            ', '.join(map(_none_str, self.label)), self.certain)


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


class TokenList:
    def __init__(self, tokens):
        self.tokens = tokens
    def __repr__(self):
        return "TokenList([ %s ])" % ', '.join(map(repr, self.tokens))


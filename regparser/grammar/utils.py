from pyparsing import alphanums, CaselessLiteral, getTokensEndLoc, Literal
from pyparsing import Suppress, WordEnd, WordStart


def keep_pos(source, location, tokens):
    """Wrap the tokens with a class that also keeps track of the match's
    location."""
    return (WrappedResult(tokens, location, getTokensEndLoc()),)


class WrappedResult():
    """Keep track of matches along with their position. This is a bit of a
    hack to get around PyParsing's tendency to drop that info."""
    def __init__(self, tokens, start, end):
        self.tokens = tokens
        self.pos = (start, end)

    def __getattr__(self, attr):
        return getattr(self.tokens, attr)


class DocLiteral(Literal):
    """Setting an objects name to a unicode string causes Sphinx to freak
    out. Instead, we'll replace with the provided (ascii) text."""
    def __init__(self, literal, ascii_text):
        super(DocLiteral, self).__init__(literal)
        self.name = ascii_text


def WordBoundaries(grammar):
    return WordStart(alphanums) + grammar + WordEnd(alphanums)


def Marker(txt):
    return Suppress(WordBoundaries(CaselessLiteral(txt)))


def SuffixMarker(txt):
    return Suppress(CaselessLiteral(txt) + WordEnd(alphanums))

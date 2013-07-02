from pyparsing import getTokensEndLoc

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




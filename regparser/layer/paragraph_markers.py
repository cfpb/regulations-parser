from layer import Layer
from regparser.tree.struct import Node


def marker_of(node):
    """Paragraphs have different markers -- regtext has parentheses,
    interpretations have periods. Appendices, in all of their flexibility,
    can have either"""
    m = [l for l in node.label if l != Node.INTERP_MARK][-1]

    if node.node_type == Node.INTERP:
        return m + '.'
    elif node.node_type == Node.APPENDIX and node.text.startswith(m + '.'):
        return m + '.'
    else:
        return '(%s)' % m


class ParagraphMarkers(Layer):
    def process(self, node):
        """Look for any leading paragraph markers."""
        marker = marker_of(node)
        if node.text.strip().startswith(marker):
            return [{
                "text": marker,
                "locations": [0]
            }]

from layer import Layer
from regparser.tree.struct import Node


class ParagraphMarkers(Layer):

    def process(self, node):
        """Look for any leading paragraph markers."""
        if node.node_type == Node.APPENDIX:
            return
        marker = ParagraphMarkers.marker(node)
        if node.text.strip().startswith(marker):
            return [{
                "text": marker,
                "locations": [0]
            }]

    @staticmethod
    def marker(node):
        m = [l for l in node.label if l != Node.INTERP_MARK][-1]

        if 'Interpretations' in node.label or 'Interp' in node.label:
            m = m + '.'
        else:
            m = '(%s)' % m
        return m

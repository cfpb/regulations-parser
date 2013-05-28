from layer import Layer

class ParagraphMarkers(Layer):

    def process(self, node):
        """Look for any leading paragraph markers."""
        marker = ParagraphMarkers.marker(node)
        if node['text'].strip().startswith(marker):
            return [{
                "text": marker,
                "locations": [0]
            }]

    @staticmethod
    def marker(node):
        m = node['label']['parts'][-1]

        if 'Interpretations' in node['label']['parts']:
            m = m + '.'
        else:
            m = '(%s)' % m
        return m


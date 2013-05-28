from layer import Layer

class ParagraphMarkers(Layer):

    def process(self, node):
        """Look for any leading paragraph markers."""
        marker = node['label']['parts'][-1]

        if 'Interpretations' in node['label']['parts']:
            marker = marker + '.'
        else:
            marker = '(%s)' % marker

        if node['text'].strip().startswith(marker):
            return [{
                "text": marker,
                "locations": [0]
            }]

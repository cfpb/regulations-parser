from layer import Layer
from parser.tree import struct

class Interpretations(Layer):
    """Supplement I (interpretations) provides (sometimes very lengthy) extra
    information about particular paragraphs. This layer provides those
    interpretations."""
    def process(self, node):
        """Is there an interpretation associated with this node? If yes,
        return the associated layer information. @TODO: Right now, this only
        associates if there is a direct match. It should also associate if any
        parents match"""
        if len(node['label']['parts']) < 3:
            return None

        part = node['label']['parts'][0]
        section = node['label']['parts'][1]
        paragraphs = node['label']['parts'][2:]

        interp_label = part + "-Interpretations-" + section
        if section.isdigit():
            interp_label += self.regtext_label(paragraphs)
        else:
            interp_label += self.appendix_label(paragraphs)

        interpretation = struct.find(self.tree, interp_label)
        if interpretation:
            return [{
                    'text': struct.join_text(interpretation),
                    'reference': interpretation['label']['text']
                    }]  # list as we will eventually match parents as well


    def regtext_label(self, paragraphs):
        """Create a label corresponding to regtext paragraphs (parens)"""
        label = ''
        for paragraph in paragraphs:
            label += '(' + paragraph + ')'
        return label

    def appendix_label(self, paragraphs):
        """Create a label corresponding to appendix paragraphs (dots)"""
        label = '-' + paragraphs[0]
        for paragraph in paragraphs[1:]:
            label += '.' + paragraph
        return label

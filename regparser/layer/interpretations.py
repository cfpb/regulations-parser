from regparser.layer.layer import Layer
from regparser.tree import struct


class Interpretations(Layer):
    """Supplement I (interpretations) provides (sometimes very lengthy) extra
    information about particular paragraphs. This layer provides those
    interpretations."""

    def process(self, node):
        """Is there an interpretation associated with this node? If yes,
        return the associated layer information. @TODO: Right now, this only
        associates if there is a direct match. It should also associate if any
        parents match"""

        interp_label = '-'.join(node.label + [struct.Node.INTERP_MARK])

        interpretation = struct.find(self.tree, interp_label)
        if interpretation and not self.empty_interpretation(interpretation):
            return [{
                    'text': struct.join_text(interpretation),
                    'reference': interpretation.label_id()
                    }]  # list as we will eventually match parents as well

    def empty_interpretation(self, interp):
        """We don't want to include empty (e.g. \n\n) nodes as
        interpretations unless their children are subparagraphs. We
        distinguish subparagraphs from structural children by checking the
        location of the 'Interp' delimiter."""
        if interp.text.strip():
            return False
        return all(
            not child.label or child.label[-1] == struct.Node.INTERP_MARK
            for child in interp.children)

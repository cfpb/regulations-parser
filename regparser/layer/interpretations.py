from regparser.layer.layer import Layer
from regparser.tree import struct
from regparser.tree.interpretation import text_to_labels


class Interpretations(Layer):
    """Supplement I (interpretations) provides (sometimes very lengthy) extra
    information about particular paragraphs. This layer provides those
    interpretations."""
    def __init__(self, tree):
        Layer.__init__(self, tree)
        self.lookup_table = {}

    def pre_process(self):
        """Create a lookup table for each interpretation"""
        def per_node(node):
            if (node.node_type != struct.Node.INTERP
                or node.label[-1] != struct.Node.INTERP_MARK):
                    return

            #   Always add a connection based on the interp's label
            self.lookup_table[tuple(node.label[:-1])] = node

            #   Also add connections based on the title
            for label in text_to_labels(node.title or '', node.label[0],
                                        warn=False):
                self.lookup_table[tuple(label[:-1])] = node
        struct.walk(self.tree, per_node)

    def process(self, node):
        """Is there an interpretation associated with this node? If yes,
        return the associated layer information. @TODO: Right now, this only
        associates if there is a direct match. It should also associate if any
        parents match"""

        label = tuple(node.label)
        if label in self.lookup_table and not self.empty_interpretation(
            self.lookup_table[label]):
                return [{
                         'reference': self.lookup_table[label].label_id()
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

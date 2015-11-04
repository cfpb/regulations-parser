# vim: set encoding=utf-8
from layer import Layer
from regparser.tree.struct import Node


class TableOfContentsLayer(Layer):
    def check_toc_candidacy(self, node):
        """ To be eligible to contain a table of contents, all of a node's
        children must have a title element. If one of the children is an
        empty subpart, we check all it's children.  """

        for c in node.children:
            if c.node_type == Node.EMPTYPART:
                for s in c.children:
                    if not s.title:
                        return False
            elif not c.title:
                return False
        return True

    def process(self, node):
        """ Create a table of contents for this node, if it's eligible. We
        ignore subparts. """

        if self.check_toc_candidacy(node):
            layer_element = []
            for c in node.children:
                if c.node_type == Node.EMPTYPART:
                    for s in c.children:
                        layer_element.append(
                            {'index': s.label, 'title': s.title})
                else:
                    layer_element.append({'index': c.label, 'title': c.title})
            return layer_element
        return None

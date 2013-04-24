class Layer():
    """ An interface definition for a layer. """
    def pre_process(self, tree):
        """ Take the whole tree and do any pre-processing """
        return NotImplemented

    def process(self, node):
        """ Construct the element of the layer relevant to processing the given node, so it returns 
        (pargraph_id, layer_content) or None if there is no relevant information. """
        return NotImplemented


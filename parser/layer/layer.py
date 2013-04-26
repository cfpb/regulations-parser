class Layer():
    def __init__(self, tree):
        self.tree = tree
        self.layer = {}

    """ An interface definition for a layer. """
    def pre_process(self):
        """ Take the whole tree and do any pre-processing """
        pass

    def process(self, node):
        """ Construct the element of the layer relevant to processing the given node, so it returns 
        (pargraph_id, layer_content) or None if there is no relevant information. """
        return NotImplemented

    def find_node(self, node, start_node_parts):
        """ Find a given node in the regulation tree. """

        if node['label']['parts'] == start_node_parts:
            return node
        for c in node['children']:
            found_node = self.find_node(c, start_node_parts)
            if found_node:
                return found_node 

    def builder(self, node):
        layer_element = self.process(node)
        if layer_element:
            self.layer[node['label']['text']] = layer_element

        for c in node['children']:
            self.builder(c)

    def build(self):
        self.builder(self.tree)
        return self.layer

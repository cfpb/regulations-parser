class Layer():
    def __init__(self, tree, cfr_title=None, version=None, notices=None,
                 act_citation=None):
        self.tree = tree
        self.notices = notices
        self.act_citation = act_citation
        self.cfr_title = cfr_title
        self.version = version
        self.layer = {}

    """ An interface definition for a layer. """
    def pre_process(self):
        """ Take the whole tree and do any pre-processing """
        pass

    def process(self, node):
        """ Construct the element of the layer relevant to processing the given
        node, so it returns (pargraph_id, layer_content) or None if there is no
        relevant information. """

        return NotImplemented

    def builder(self, node):
        layer_element = self.process(node)
        if layer_element:
            self.layer[node.label_id()] = layer_element

        for c in node.children:
            self.builder(c)

    def build(self):
        self.pre_process()
        self.builder(self.tree)
        return self.layer

class Layer():
    def __init__(self, tree, cfr_title=None, version=None, notices=None,
                 act_citation=None):
        self.tree = tree
        if not notices:
            self.notices = []
        else:
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

    # @profile
    def builder(self, node, cache=None):
        if cache:
            layer_element = cache.fetch_or_process(self, node)
        else:
            layer_element = self.process(node)
        if layer_element:
            self.layer[node.label_id()] = layer_element

        for c in node.children:
            self.builder(c, cache)

    # @profile
    def build(self, cache=None):
        self.pre_process()
        self.builder(self.tree, cache)
        return self.layer

class LayerGenerator():

    def __init__(self, regulation_tree, generator):
        self.tree = regulation_tree
        self.layer_generator = generator
        self.layer = {}

    def generate_layer(self):
        """ Walk the regulation tree, generating a layer at each node. """
        self.process_node(self.tree)
        return self.layer 

    def process_node(self, node):
        citations_list = self.layer_generator.parse(node['text'], node['label']['parts'])
        if citations_list:
            part_index = '-'.join(node['label']['parts'])
            self.layer[part_index] = citations_list

        for c in node['children']:
            self.process_node(c)

class WholeTreeLayerGenerator():
    def __init__(self, regulation_tree, generator):
        self.tree = regulation_tree
        self.layer_generator = generator

    def generate_layer(self, start_node):
        starting_node = self.find_starting_node(self.tree, start_node)
        layer = self.layer_generator.generate_layer(starting_node)
        part_index = '-'.join(starting_node['label']['parts'])
        
        return {part_index:layer}

    def find_starting_node(self, node, start_node):
        if node['label']['parts'] == start_node:
            return node

        for c in node['children']:
            starting_node = self.find_starting_node(c, start_node)
            if starting_node:
                return starting_node

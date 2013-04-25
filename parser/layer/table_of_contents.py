from layer import Layer

class TableOfContentsLayer(Layer):

    def process(self, node):
        layer_element = []

        for c in node['children']:
            layer_element.append({'index':c['label']['parts'], 'title':c['label']['title']})

        return layer_element

    def build(self, **kwargs):
        sections = kwargs['sections_list']

        for s in sections:
            starting_node = self.find_node(self.tree, s)
            layer_element = self.process(starting_node)
            if layer_element:
                part_index = '-'.join(starting_node['label']['parts'])
                self.layer[part_index] = layer_element
        return self.layer

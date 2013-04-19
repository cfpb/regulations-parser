
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


if __name__ == "__main__":
    import parsing.api_stub
    import parsing.layer.external_citations
    import parsing.layer.internal_citations
    import json

    reg_json = api_stub.get_regulation_as_json('/vagrant/data/regulations/rege/rege.json')
    ext_citation_parser = external_citations.ExternalCitationParser()
    int_citation_parser = internal_citations.InternalCitationParser()
    #layer_generator = LayerGenerator(reg_json, ext_citation_parser)
    layer_generator = LayerGenerator(reg_json, int_citation_parser)
    layer = layer_generator.generate_layer()
    print json.dumps(layer)

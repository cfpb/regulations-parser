import parser.api_stub
import parser.layer.table_of_contents
import parsing.layer.external_citations
from parser.layer.whole_layer_generator import WholeTreeLayerGenerator
import json

def generate_external_citations(reg_json):
    """ Generate the external citations layer """
    citation_parser = external_citations.ExternalCitationParser()
    layer_generator = LayerGenerator(reg_json, citation_parser)
    layer = layer_generator.generate_layer()
    print json.dumps(layer)

def generate_internal_citations(reg_json):
    """ Generate the internal citations layer """
    citation_parser = internal_citations.InternalCitationParser()
    layer_generator = LayerGenerator(reg_json, citation_parser)
    layer = layer_generator.generate_layer()
    print json.dumps(layer)

def generate_table_of_contents(reg_json):
    """ Generate the Table of Contents layer """
    layer_generator = WholeTreeLayerGenerator(reg_json, table_of_contents)
    appendix_toc = layer_generator.generate_layer(['1005', 'A'])
    toc = layer_generator.generate_layer(['1005'])

    contents_layer = {}
    contents_layer.update(appendix_toc)
    contents_layer.update(toc)

    print json.dumps(contents_layer)


if __name__ == "__main__":
    reg_json = api_stub.get_regulation_as_json('/vagrant/data/regulations/regulation/1005/20111227')
    generate_table_of_contents(reg_json)


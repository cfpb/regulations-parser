from parser import api_stub
import parser.layer.table_of_contents
from parser.layer import internal_citations
from parser.layer import external_citations
from parser.layer import table_of_contents
import json

def generate_external_citations(reg_json):
    """ Generate the enxternal citations layer """

    layer_generator = internal_citations.ExternalCitationParser(reg_json)
    layer = layer_generator.build()
    print json.dumps(layer)

def generate_internal_citations(reg_json):
    """ Generate the internal ciations layer. """
    layer_generator = internal_citations.InternalCitationParser(reg_json)
    layer = layer_generator.build()
    print json.dumps(layer)

def generate_table_of_contents(reg_json):
    """ Generate the Table of Contents layer """

    layer_generator = table_of_contents.TableOfContentsLayer(reg_json)
    toc = layer_generator.build()
    print json.dumps(toc)

if __name__ == "__main__":
    reg_json = api_stub.get_regulation_as_json('/vagrant/data/regulations/regulation/1005/20111227')
    generate_table_of_contents(reg_json)
    #generate_internal_citations(reg_json)
    #generate_external_citations(reg_json)

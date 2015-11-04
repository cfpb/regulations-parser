from regparser import api_stub
from regparser.layer import external_citations
from regparser.layer import internal_citations
from regparser.layer import interpretations
from regparser.layer import table_of_contents
from regparser.layer import terms
from regparser.layer import key_terms
from regparser.tree.struct import NodeEncoder


def generate_external_citations(reg_json):
    """ Generate the enxternal citations layer """

    layer_generator = external_citations.ExternalCitationParser(reg_json)
    layer = layer_generator.build()
    print NodeEncoder().encode(layer)


def generate_internal_citations(reg_json):
    """ Generate the internal ciations layer. """
    layer_generator = internal_citations.InternalCitationParser(reg_json)
    layer = layer_generator.build()
    print NodeEncoder().encode(layer)


def generate_table_of_contents(reg_json):
    """ Generate the Table of Contents layer """

    layer_generator = table_of_contents.TableOfContentsLayer(reg_json)
    toc = layer_generator.build()
    print NodeEncoder().encode(toc)


def generate_interpretations(reg):
    """ Generate the Interpretations layer """
    layer_generator = interpretations.Interpretations(reg)
    print NodeEncoder().encode(layer_generator.build())


def generate_terms(reg):
    """ Generate the Terms layer """
    layer_generator = terms.Terms(reg)
    print NodeEncoder().encode(layer_generator.build())


def generate_key_terms(reg):
    """ Generate the key terms layer """
    layer_generator = key_terms.KeyTerms(reg)
    layer_generator.build()
    print NodeEncoder().encode(layer_generator.build())

if __name__ == "__main__":
    reg_json = api_stub.get_regulation_as_json('/tmp/xtree.json')
    # generate_table_of_contents(reg_json)
    # generate_internal_citations(reg_json)
    # generate_external_citations(reg_json)
    # generate_interpretations(reg_json)
    # generate_terms(reg_json)
    generate_key_terms(reg_json)

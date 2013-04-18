import api_stub
import table_of_contents
from whole_layer_generator import WholeTreeLayerGenerator
import json


def generate_table_of_contents(reg_json):
    layer_generator = WholeTreeLayerGenerator(reg_json, table_of_contents)
    appendix_toc = layer_generator.generate_layer(['1005', 'A'])
    toc = layer_generator.generate_layer(['1005'])

    contents_layer = {}
    contents_layer.update(appendix_toc)
    contents_layer.update(toc)

    print json.dumps(contents_layer)

if __name__ == "__main__":
    reg_json = api_stub.get_regulation_as_json('/vagrant/data/regulations/rege/rege.json')
    generate_table_of_contents(reg_json)


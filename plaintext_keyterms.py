from reg_parser.layer import key_terms
from reg_parser import api_stub
from reg_parser.tree import struct
import json

def generate_key_terms_layer(xml_based_reg_json):
    layer_generator = key_terms.KeyTerms(xml_based_reg_json)
    return layer_generator.build()

#We're not going to use our heuristic to determine key terms for paragraphs 
#this has already properly been done for. 
xml_based_reg = api_stub.get_regulation_as_json('/tmp/xtree.json')
real_key_terms_layer = generate_key_terms_layer(xml_based_reg)

layer = {}
part_end = '1005.'

def generate_keyterm(node):
    if node['label']['text'] not in real_key_terms_layer:
        node_text = key_terms.KeyTerms.process_node_text(node).encode('utf-8')
        d = '.'
        sentences = [e+d for e in node_text.split(d) if e != '']

        if len(sentences) > 1:
            #Ignore any paragraph that has only one sentence
            first_sentence = sentences[0]
            words = first_sentence.split()
            if not words[-1] == part_end and not first_sentence.startswith('!['):
                num_words = len(words)

                #key terms are short
                if num_words <= 15:
                    layer_element = {
                        "key_term": first_sentence,
                        "locations": [0]
                    }
                    layer[node['label']['text']] = [layer_element]

if __name__ == "__main__":
    #Use the plain text based JSON for the regulation. 
    tree = api_stub.get_regulation_as_json('/vagrant/data/stub-server/regulation/1005/2013-10604-eregs')
    struct.walk(tree, generate_keyterm)

    print json.dumps(layer)


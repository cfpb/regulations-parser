from layer import Layer
import re

class KeyTerms(Layer):
    def __init__(self, tree):
        Layer.__init__(self, tree)
        self.pattern = re.compile(ur'.*?<E T="03">([^<]*?)</E>.*?', re.UNICODE) 

    def process(self, node):
        matches = self.pattern.match(node['text'])
        if matches:
            keyterm = matches.groups()[0]
            start = node['text'].find(keyterm)
            end = start + len(keyterm)

            offsets = [[start, end]]

            layer_el = [{
                "key_term": keyterm, 
                #The first instance of the key term is right one. 
                "location": [1]
            }]
            return layer_el

from layer import Layer
import re

class KeyTerms(Layer):
    def __init__(self, tree):
        Layer.__init__(self, tree)
        self.pattern = re.compile(ur'.*?<E T="03">([^<]*?)</E>.*?', re.UNICODE) 

    def process_node_text(self, node):
        """ Take a paragraph, remove the marker, and extraneous whitespaces. """
        marker = node['label']['parts'][-1]
        marker = '(%s)' % marker
        text = node['text']

        text = text.replace(marker, '', 1).strip()
        return text

    def keyterm_is_first(self, node, keyterm):
        """ The keyterm should be the first phrase in the paragraph. """
        node_text = self.process_node_text(node)
        start = node_text.find(keyterm)
        tag_length = len("<E T='03'>")

        return start == tag_length

    def process(self, node):
        matches = self.pattern.match(node['text'])
        if matches:
            keyterm = matches.groups()[0]

            if self.keyterm_is_first(node, keyterm):
                layer_el = [{
                    "key_term": keyterm, 
                    #The first instance of the key term is right one. 
                    "locations": [0]
                }]
                return layer_el

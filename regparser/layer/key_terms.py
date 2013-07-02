from layer import Layer
from regparser.layer.paragraph_markers import ParagraphMarkers
import re

class KeyTerms(Layer):
    def __init__(self, tree):
        Layer.__init__(self, tree)

    @staticmethod
    def process_node_text(node):
        """ Take a paragraph, remove the marker, and extraneous whitespaces. """
        marker = ParagraphMarkers.marker(node)
        text = node['text']

        text = text.replace(marker, '', 1).strip()
        return text

    @staticmethod
    def keyterm_is_first(node, keyterm):
        """ The keyterm should be the first phrase in the paragraph. """
        node_text = KeyTerms.process_node_text(node)
        start = node_text.find(keyterm)
        tag_length = len("<E T='03'>")

        return start == tag_length

    @staticmethod
    def get_keyterm(node):
        pattern = re.compile(ur'.*?<E T="03">([^<]*?)</E>.*?', re.UNICODE) 
        matches = pattern.match(node['text'])
        if matches and KeyTerms.keyterm_is_first(node, matches.groups()[0]):
            return matches.groups()[0]

    def process(self, node):
        keyterm = KeyTerms.get_keyterm(node)
        if keyterm:
            layer_el = [{
                    "key_term": keyterm, 
                    #The first instance of the key term is right one. 
                    "locations": [0] }]
            return layer_el


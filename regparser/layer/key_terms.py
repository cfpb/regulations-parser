from layer import Layer
from regparser.layer.paragraph_markers import marker_of
from regparser.layer.terms import Terms
import re


def eliminate_extras(keyterm):
    """ The XML <E> tags that indicate keyterms are also used
    for italics. So, phrases such as 'See' and 'See also' are included
    sometimes in the keyterm. We eliminate that here. """

    extras = [' See also', ' See']
    for extra in extras:
        if keyterm.endswith(extra):
            keyterm = keyterm[:-len(extra)]
    return keyterm


class KeyTerms(Layer):
    @staticmethod
    def process_node_text(node):
        """Take a paragraph, remove the marker, and extraneous whitespaces."""
        marker = marker_of(node)
        text = node.tagged_text

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
        matches = pattern.match(node.tagged_text)
        if matches and KeyTerms.keyterm_is_first(node, matches.groups()[0]):
            included, excluded = Terms(None).node_definitions(node)
            terms = included + excluded
            keyterm_as_term = matches.groups()[0].lower()
            if not any(ref.term == keyterm_as_term for ref in terms):
                return matches.groups()[0]

    def process(self, node):
        """ Get keyterms if we have text in the node that preserves the
        <E> tags. """
        if hasattr(node, 'tagged_text'):
            keyterm = KeyTerms.get_keyterm(node)
            if keyterm:
                keyterm = eliminate_extras(keyterm)
                layer_el = [{
                    "key_term": keyterm,
                    # The first instance of the key term is right one.
                    "locations": [0]}]
                return layer_el

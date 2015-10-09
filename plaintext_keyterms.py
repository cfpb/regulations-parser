# vim: set encoding=utf-8
import re

from pyparsing import Literal

from regparser import api_stub
from regparser.citations import internal_citations, Label
from regparser.grammar.external_citations import regtext_external_citation
from regparser.layer import key_terms
from regparser.tree import struct


def generate_key_terms_layer(xml_based_reg_json):
    layer_generator = key_terms.KeyTerms(xml_based_reg_json)
    return layer_generator.build()

# We're not going to use our heuristic to determine key terms for paragraphs
# this has already properly been done for.
xml_based_reg = api_stub.get_regulation_as_json('/tmp/xtree.json')
real_key_terms_layer = generate_key_terms_layer(xml_based_reg)

layer = {}
part_end = '1005.'
exclude_parser = (
    regtext_external_citation
    | Literal("U.S.")
)
period = re.compile(r'\.(?!,)')  # Not followed by a comma


def generate_keyterm(node):
    label_id = node.label_id()
    if label_id in real_key_terms_layer:
        layer[label_id] = real_key_terms_layer[label_id]
    else:
        node_text = key_terms.KeyTerms.process_node_text(node)
        if not node_text:
            return

        # Our Appendix parsing isn't particularly accurate -- avoid keyterms
        if node.node_type == struct.Node.APPENDIX:
            return

        exclude = [(start, end) for _, start, end in
                   exclude_parser.scanString(node_text)]
        exclude.extend((pc.full_start, pc.full_end) for pc in
                       internal_citations(node_text, Label()))

        periods = [m.start() for m in period.finditer(node_text)]
        # Remove any periods which are part of a citation
        periods = filter(lambda p: all(p < start or p > end
                                       for start, end in exclude), periods)

        # Key terms must either have a full "sentence" or end with a hyphen
        if not periods and node_text[-1] != u'—':
            return

        if periods:
            first_p = periods[0]
            # Check for cases where the period is "inside" something;
            # include the period
            next_char = node_text[first_p + 1: first_p + 2]
            if next_char in (')', u'”'):
                first_sentence = node_text[:first_p + 2]
            else:
                first_sentence = node_text[:first_p + 1]
        else:
            first_sentence = node_text

        # Key terms can't be the entire text of a leaf node
        if first_sentence == node_text and not node.children:
            return

        words = first_sentence.split()
        if (not words[-1] == part_end and
                not first_sentence.startswith('![')):
            num_words = len(words)

            # key terms are short
            if num_words <= 15:
                layer_element = {
                    "key_term": first_sentence,
                    "locations": [0]
                }
                layer[label_id] = [layer_element]

if __name__ == "__main__":
    # Use the plain text based JSON for the regulation.
    tree = api_stub.get_regulation_as_json(
        '/vagrant/data/stub-server/regulation/1005/2013-10604-eregs')
    struct.walk(tree, generate_keyterm)

    print struct.NodeEncoder().encode(layer)

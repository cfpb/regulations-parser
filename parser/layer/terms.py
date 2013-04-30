from layer import Layer
from parser import utils
from parser.grammar.terms import term_parser
from parser.tree import struct

class Terms(Layer):

    def __init__(self, tree):
        Layer.__init__(self, tree)
        self.scoped_terms = {}  #   scope -> List[(term, definition_ref)]

    def pre_process(self):
        """Step through every node in the tree, finding definitions. Add
        these definition to self.scoped_terms"""
        def per_node(node):
            if self.has_definitions(node):
                scope = self.definitions_scope(node)
                definitions = self.node_definitions(node)
                existing = self.scoped_terms.get(scope, [])
                self.scoped_terms[scope] = existing + definitions

        struct.walk(self.tree, per_node)

    def has_definitions(self, node):
        """Does this node have definitions?"""
        return 'definition' in node['text'].lower()

    def node_definitions(self, node):
        """Walk through this node and its children to find defined terms."""
        def per_node(n):
            return [(match[0].lower(), n['label']['text']) 
                    for match,_,_ in term_parser.scanString(n['text'])]
        return utils.flatten(struct.walk(node, per_node))

    def definitions_scope(self, node):
        """Try to determine the scope of definitions in this term."""
        if "purposes of this part" in node['text'].lower():
            return tuple(node['label']['parts'][:1])
        elif "purposes of this section" in node['text'].lower():
            return tuple(node['label']['parts'][:2])
        elif "purposes of this paragraph" in node['text'].lower():
            return tuple(node['label']['parts'])
        return tuple(node['label']['parts'][:1])    # defaults to whole reg

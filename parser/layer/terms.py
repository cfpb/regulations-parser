from layer import Layer
from parser import utils
from parser.grammar.external_citations import uscode_exp as uscode
from parser.grammar.terms import term_parser
from parser.layer.paragraph_markers import ParagraphMarkers
from parser.tree import struct
import re

class Terms(Layer):

    def __init__(self, tree):
        Layer.__init__(self, tree)
        self.layer['referenced'] = {}
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
        # Definitions cannot be in the top-most layer of the tree (the root)
        if len(node['label']['parts']) < 2:
            return False
        # Definitions are only in the reg text (not appendices/interprs)
        if not node['label']['parts'][1].isdigit():
            return False
        stripped = node['text'].strip(ParagraphMarkers.marker(node)).strip()
        return (
                stripped.lower().startswith('definition')
                or ('title' in node['label'] 
                    and 'definition' in node['label']['title'].lower()))

    def node_definitions(self, node):
        """Walk through this node and its children to find defined terms.
        'Act' is a special case, as it is also defined as an external
        citation."""
        def per_node(n):
            matches = [(match[0].lower(), n['label']['text']) 
                    for match,_,_ in term_parser.scanString(n['text'])]
            final_matches = []
            for term, label in matches:
                if term != 'act' or not list(uscode.scanString(n['text'])):
                    final_matches.append((term, label))
            return final_matches
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

    def process(self, node):
        """Determine which (if any) definitions would apply to this node,
        then find if any of those terms appear in this node"""
        applicable_terms = {}
        for segment_length in range(1, len(node['label']['parts'])+1):
            scope = tuple(node['label']['parts'][:segment_length])
            for term, definition_ref in self.scoped_terms.get(scope, []):
                applicable_terms[term] = definition_ref # overwrites

        layer_el = []
        term_list = [(term,ref) for term, ref in applicable_terms.iteritems()]
        matches = self.calculate_offsets(node['text'], term_list)
        for term, ref, offsets in matches:
            term_ref = term + ":" + ref
            if term_ref not in self.layer['referenced']:
                self.layer['referenced'][term_ref] = {
                        "term": term,
                        "reference": ref,
                        "text": struct.join_text(struct.find(self.tree, ref))
                        }
            layer_el.append({
                "ref": term_ref,
                "offsets": offsets
                })
        return layer_el


    def calculate_offsets(self, text, applicable_terms):
        """Search for defined terms in this text, with a preference for all
        larger (i.e. containing) terms."""

        #   longer terms first
        applicable_terms.sort(key=lambda x: len(x[0]), reverse=True)

        matches = []
        existing_defs = []
        for term, ref in applicable_terms:
            re_term = ur'\b' + re.escape(term) + ur'\b'
            offsets = [(m.start(), m.end()) 
                    for m in re.finditer(re_term, text.lower())]
            safe_offsets = []
            for start, end in offsets:
                if any(start >= e[0] and start <= e[1] 
                        for e in existing_defs):
                    continue
                if any(end >= e[0] and end <= e[1] for e in existing_defs):
                    continue
                safe_offsets.append((start, end))
            if not safe_offsets:
                continue

            existing_defs.extend(safe_offsets)
            matches.append((term, ref, safe_offsets))
        return matches


# vim: set fileencoding=utf-8
from collections import defaultdict
import re

from inflection import pluralize

from regparser import utils
from regparser.grammar.external_citations import uscode_exp as uscode
from regparser.grammar.terms import term_parser
from regparser.layer.layer import Layer
from regparser.layer.paragraph_markers import ParagraphMarkers
from regparser.tree import struct
import settings


class Ref(object):
    def __init__(self, term, label, position):
        self.term = term
        self.label = label
        self.position = position

    def __eq__(self, other):
        """Equality depends on equality of the fields"""
        return (hasattr(other, 'term') and hasattr(other, 'label')
                and hasattr(other, 'position') and self.term == other.term
                and self.label == other.label
                and self.position == other.position)


class Terms(Layer):

    def __init__(self, tree):
        Layer.__init__(self, tree)
        self.layer['referenced'] = {}
        #   scope -> List[(term, definition_ref)]
        self.scoped_terms = defaultdict(list)
        #   subpart -> list[section]
        self.subpart_map = defaultdict(list)


    def add_subparts(self):
        """Document the relationship between sections and subparts"""

        current_subpart = [None]    # Need a reference for the closure

        def per_node(node):
            if node.node_type == struct.Node.SUBPART:
                current_subpart[0] = node.label[2]
            elif node.node_type == struct.Node.EMPTYPART:
                current_subpart[0] = None
            if (len(node.label) == 2 and
                node.node_type in (struct.Node.REGTEXT, struct.Node.APPENDIX)):
                #Subparts
                section = node.label[-1]
                self.subpart_map[current_subpart[0]].append(section)

        struct.walk(self.tree, per_node)

    def pre_process(self):
        """Step through every node in the tree, finding definitions. Add
        these definition to self.scoped_terms. Also keep track of which
        subpart we are in. Finally, document all defined terms. """

        self.add_subparts()

        def per_node(node):
            if self.has_definitions(node):
                for scope in self.definitions_scopes(node):
                    included, excluded = self.node_definitions(node)
                    self.scoped_terms[scope].extend(included)
                    self.scoped_terms['EXCLUDED'].extend(excluded)

        struct.walk(self.tree, per_node)

        for scope in self.scoped_terms:
            for ref in self.scoped_terms[scope]:
                self.layer['referenced'][ref.term + ":" + ref.label] = {
                    'term': ref.term,
                    'reference': ref.label,
                    'position': ref.position
                }

    def has_definitions(self, node):
        """Does this node have definitions?"""
        # Definitions cannot be in the top-most layer of the tree (the root)
        if len(node.label) < 2:
            return False
        # Definitions are only in the reg text (not appendices/interprs)
        if node.node_type != struct.Node.REGTEXT:
            return False
        stripped = node.text.strip(ParagraphMarkers.marker(node)).strip()
        return (
            stripped.lower().startswith('definition')
            or (node.title and 'definition' in node.title.lower())
            or re.search('the term .* means', stripped.lower())
            )

    def is_exclusion(self, term, text, previous_terms):
        """Some definitions are exceptions/exclusions of a previously
        defined term. At the moment, we do not want to include these as they
        would replace previous (correct) definitions."""
        if term not in [t.term for t in previous_terms]:
            return False
        regex = 'the term .?' + re.escape(term) + '.? does not include'
        return bool(re.search(regex, text.lower()))

    def node_definitions(self, node):
        """Walk through this node and its children to find defined terms.
        'Act' is a special case, as it is also defined as an external
        citation."""
        included_defs = []
        excluded_defs = []

        def per_node(n):
            for match, _, _ in term_parser.scanString(n.text):
                term = match.term.tokens[0].lower()
                pos = match.term.pos

                add_to = included_defs

                if term == 'act' and list(uscode.scanString(n.text)):
                    add_to = excluded_defs
                if self.is_exclusion(term, n.text, included_defs):
                    add_to = excluded_defs
                add_to.append(Ref(term, n.label_id(), pos))
        struct.walk(node, per_node)
        return included_defs, excluded_defs

    def subpart_scope(self, label_parts):
        """Given a label, determine which sections fall under the same
        subpart"""
        reg = label_parts[0]
        section = label_parts[1]
        for subpart in self.subpart_map:
            if section in self.subpart_map[subpart]:
                return [[reg, sect] for sect in self.subpart_map[subpart]]
        return []

    def definitions_scopes(self, node):
        """Try to determine the scope of definitions in this term."""
        scopes = []
        if "purposes of this part" in node.text.lower():
            scopes.append(node.label[:1])
        elif "purposes of this subpart" in node.text.lower():
            scopes.extend(self.subpart_scope(node.label))
        elif "purposes of this section" in node.text.lower():
            scopes.append(node.label[:2])
        elif "purposes of this paragraph" in node.text.lower():
            scopes.append(node.label)
        else:   # defaults to whole reg
            scopes.append(node.label[:1])

        for scope in list(scopes):  # second list so we can iterate
            interp_scope = scope + [struct.Node.INTERP_MARK]
            if interp_scope:
                scopes.append(interp_scope)
        return [tuple(scope) for scope in scopes]

    def process(self, node):
        """Determine which (if any) definitions would apply to this node,
        then find if any of those terms appear in this node"""
        applicable_terms = {}
        for segment_length in range(1, len(node.label)+1):
            scope = tuple(node.label[:segment_length])
            for ref in self.scoped_terms.get(scope, []):
                applicable_terms[ref.term] = ref    # overwrites

        layer_el = []
        #   Remove any definitions defined in this paragraph
        term_list = [
            (term, ref) for term, ref in applicable_terms.iteritems()
            if ref.label != node.label_id()]

        exclusions = self.excluded_offsets(node.label_id(), node.text)

        matches = self.calculate_offsets(node.text, term_list, exclusions)
        for term, ref, offsets in matches:
            layer_el.append({
                "ref": ref.term + ':' + ref.label,
                "offsets": offsets
                })
        return layer_el

    def excluded_offsets(self, label, text):
        """We explicitly exclude certain chunks of text (for example, words
        we are defining shouldn't have links appear within the defined
        term.) More will be added in the future"""
        exclusions = []
        for reflist in self.scoped_terms.values():
            exclusions.extend(
                ref.position for ref in reflist if ref.label == label)
        for ignore_term in settings.IGNORE_DEFINITIONS_IN:
            exclusions.extend(
                (match.start(), match.end()) for match in
                re.finditer(r'\b' + re.escape(ignore_term) + r'\b', text))
        return exclusions

    def calculate_offsets(self, text, applicable_terms, exclusions=[]):
        """Search for defined terms in this text, with a preference for all
        larger (i.e. containing) terms."""

        # don't modify the original
        exclusions = list(exclusions)

        # add plurals to applicable terms
        pluralized = [(pluralize(t[0]), t[1]) for t in applicable_terms]
        applicable_terms += pluralized

        #   longer terms first
        applicable_terms.sort(key=lambda x: len(x[0]), reverse=True)

        matches = []
        for term, ref in applicable_terms:
            re_term = ur'\b' + re.escape(term) + ur'\b'
            offsets = [
                (m.start(), m.end())
                for m in re.finditer(re_term, text.lower())]
            safe_offsets = []
            for start, end in offsets:
                #   Start is contained in an existing def
                if any(start >= e[0] and start <= e[1] for e in exclusions):
                    continue
                #   End is contained in an existing def
                if any(end >= e[0] and end <= e[1] for e in exclusions):
                    continue
                safe_offsets.append((start, end))
            if not safe_offsets:
                continue

            exclusions.extend(safe_offsets)
            matches.append((term, ref, safe_offsets))
        return matches

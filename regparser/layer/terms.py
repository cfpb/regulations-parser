# vim: set fileencoding=utf-8
from collections import defaultdict
import re

from inflection import pluralize

from regparser import utils
from regparser.grammar import terms as grammar
from regparser.grammar.external_citations import uscode_exp as uscode
from regparser.layer.layer import Layer
from regparser.tree import struct
from regparser.tree.priority_stack import PriorityStack
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

    def __repr__(self):
        return 'Ref( term=%s, label=%s, position=%s )' % (
                repr(self.term), repr(self.label), repr(self.position))


class ParentStack(PriorityStack):
    """Used to keep track of the parents while processing nodes to find
    terms. This is needed as the definition may need to find its scope in
    parents."""
    def unwind(self):
        """No collapsing needs to happen."""
        self.pop()


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

    def determine_scope(self, stack):
        for node in stack.lineage():
            scopes = []
            if "purposes of this part" in node.text.lower():
                scopes.append(node.label[:1])
            elif "purposes of this subpart" in node.text.lower():
                scopes.extend(self.subpart_scope(node.label))
            elif "purposes of this section" in node.text.lower():
                scopes.append(node.label[:2])
            elif "purposes of this paragraph" in node.text.lower():
                scopes.append(node.label)

            #   Add interpretation to scopes
            scopes = scopes + [s + [struct.Node.INTERP_MARK] for s in scopes]
            if scopes:
                return [tuple(s) for s in scopes]

        #   Couldn't determine scope; default to the entire reg
        return [tuple(node.label[:1])]

    def pre_process(self):
        """Step through every node in the tree, finding definitions. Add
        these definition to self.scoped_terms. Also keep track of which
        subpart we are in. Finally, document all defined terms. """

        self.add_subparts()

        stack = ParentStack()
        def per_node(node):
            if node.node_type in (struct.Node.REGTEXT, struct.Node.SUBPART,
                                  struct.Node.EMPTYPART):
                if (len(node.label) > 1
                        and node.node_type == struct.Node.REGTEXT):
                    #   Add one for the subpart level
                    stack.add(len(node.label) + 1, node)
                else:
                    stack.add(len(node.label), node)

                included, excluded = self.node_definitions(node, stack)
                if included:
                    for scope in self.determine_scope(stack):
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

    def applicable_terms(self, label):
        """Find all terms that might be applicable to nodes with this label.
        Note that we don't have to deal with subparts as subpart_scope simply
        applies the definition to all sections in a subpart"""
        applicable_terms = {}
        for segment_length in range(1, len(label) + 1):
            scope = tuple(label[:segment_length])
            for ref in self.scoped_terms.get(scope, []):
                applicable_terms[ref.term] = ref    # overwrites
        return applicable_terms

    def is_exclusion(self, term, node):
        """Some definitions are exceptions/exclusions of a previously
        defined term. At the moment, we do not want to include these as they
        would replace previous (correct) definitions."""
        applicable_terms = self.applicable_terms(node.label)
        if term in applicable_terms:
            regex = 'the term .?' + re.escape(term) + '.? does not include'
            return bool(re.search(regex, node.text.lower()))
        return False

    def has_parent_definitions_indicator(self, stack):
        """With smart quotes, we catch some false positives, phrases in quotes
        that are not terms. This extra test lets us know that a parent of the
        node looks like it would contain definitions."""
        for node in stack.lineage():
            if ('Definition' in node.text
                or 'Definition' in (node.title or '')
                or re.search('the term .* means', node.text.lower())):
                return True
        return False

    def node_definitions(self, node, stack):
        """Walk through this node and its children to find defined terms.
        'Act' is a special case, as it is also defined as an external
        citation."""
        included_defs = []
        excluded_defs = []

        def add_match(n, term, pos):
            if ((term == 'act' and list(uscode.scanString(n.text)))
                    or self.is_exclusion(term, n)):
                excluded_defs.append(Ref(term, n.label_id(), pos))
            else:
                included_defs.append(Ref(term, n.label_id(), pos))

        if self.has_parent_definitions_indicator(stack):
            for match, _, _ in grammar.smart_quotes.scanString(node.text):
                term = match.term.tokens[0].lower().strip(',.;')
                #   Don't use pos_end because we are stripping some chars
                pos_start = match.term.pos[0]
                add_match(node,
                          term,
                          (pos_start, pos_start + len(term)))

        if hasattr(node, 'tagged_text'):
            for match, _, _ in grammar.xml_term_parser.scanString(
                    node.tagged_text):
                """Position in match reflects XML tags, so its dropped in 
                preference of new values based on node.text."""
                pos_start = node.text.find(match.term.tokens[0])
                term = node.tagged_text[
                    match.term.pos[0]:match.term.pos[1]].lower()
                match_len = len(term)
                add_match(node,
                          term,
                          (pos_start, pos_start + match_len))

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

    def process(self, node):
        """Determine which (if any) definitions would apply to this node,
        then find if any of those terms appear in this node"""
        applicable_terms = self.applicable_terms(node.label)

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

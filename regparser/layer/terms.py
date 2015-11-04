# vim: set fileencoding=utf-8
from collections import defaultdict
from itertools import chain
import re

import inflection
try:
    del inflection.PLURALS[
        inflection.PLURALS.index(('(?i)(p)erson$', '\\1eople'))]
except ValueError:
    pass


from regparser.citations import internal_citations, Label
from regparser.grammar import terms as grammar
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
    #   Regexes used in determining scope
    part_re, subpart_re = re.compile(r"\bpart\b"), re.compile(r"\bsubpart\b")
    sect_re, par_re = re.compile(r"\bsection\b"), re.compile(r"\bparagraph\b")
    #   Regex to confirm scope indicator
    scope_re = re.compile(r".*purposes of( this)?\s*$", re.DOTALL)
    scope_used_re = re.compile(
        r".*as used in( this)?\s*$", re.DOTALL | re.IGNORECASE)

    def __init__(self, *args, **kwargs):
        Layer.__init__(self, *args, **kwargs)
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
            if (node.node_type in (struct.Node.REGTEXT, struct.Node.APPENDIX)
                    and len(node.label) == 2):
                # Subparts
                section = node.label[-1]
                self.subpart_map[current_subpart[0]].append(section)

        struct.walk(self.tree, per_node)

    def scope_of_text(self, text, label_struct, verify_prefix=True):
        """Given specific text, try to determine the definition scope it
        indicates. Implicit return None if none is found."""
        scopes = []
        #   First, make a list of potential scope indicators
        citations = internal_citations(text, label_struct,
                                       require_marker=True)
        indicators = [(c.full_start, c.label.to_list()) for c in citations]
        text = text.lower()
        label_list = label_struct.to_list()
        indicators.extend((m.start(), label_list[:1])
                          for m in Terms.part_re.finditer(text))
        indicators.extend((m.start(), label_list[:2])
                          for m in Terms.sect_re.finditer(text))
        indicators.extend((m.start(), label_list)
                          for m in Terms.par_re.finditer(text))
        #   Subpart's a bit more complicated, as it gets expanded into a
        #   list of sections
        for match in Terms.subpart_re.finditer(text):
            indicators.extend(
                (match.start(), subpart_label)
                for subpart_label in self.subpart_scope(label_list))

        #   Finally, add the scope if we verify its prefix
        for start, label in indicators:
            if not verify_prefix or Terms.scope_re.match(text[:start]):
                scopes.append(label)
            elif Terms.scope_used_re.match(text[:start]):
                scopes.append(label)

        #   Add interpretation to scopes
        scopes = scopes + [s + [struct.Node.INTERP_MARK] for s in scopes]
        if scopes:
            return [tuple(s) for s in scopes]

    def determine_scope(self, stack):
        for node in stack.lineage():
            scopes = self.scope_of_text(node.text, Label.from_node(node))
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
            if len(node.label) > 1 and node.node_type == struct.Node.REGTEXT:
                #   Add one for the subpart level
                stack.add(len(node.label) + 1, node)
            elif node.node_type in (struct.Node.SUBPART,
                                    struct.Node.EMPTYPART):
                #   Subparts all on the same level
                stack.add(2, node)
            else:
                stack.add(len(node.label), node)

            if node.node_type in (struct.Node.REGTEXT, struct.Node.SUBPART,
                                  struct.Node.EMPTYPART):
                included, excluded = self.node_definitions(node, stack)
                if included:
                    for scope in self.determine_scope(stack):
                        self.scoped_terms[scope].extend(included)
                self.scoped_terms['EXCLUDED'].extend(excluded)

        struct.walk(self.tree, per_node)

        referenced = self.layer['referenced']
        for scope in self.scoped_terms:
            for ref in self.scoped_terms[scope]:
                key = ref.term + ":" + ref.label
                if (key not in referenced     # New term
                        # Or this term is earlier in the paragraph
                        or ref.position[0] < referenced[key]['position'][0]):
                    referenced[key] = {
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
                    or re.search('the term .* (means|refers to)',
                                 node.text.lower())
                    or re.search(u'“[^”]+” (means|refers to)',
                                 node.text.lower())):
                return True
        return False

    def node_definitions(self, node, stack=None):
        """Find defined terms in this node's text."""
        included_defs = []
        excluded_defs = []

        def add_match(n, term, pos):
            if (self.is_exclusion(term, n)):
                excluded_defs.append(Ref(term, n.label_id(), pos))
            else:
                included_defs.append(Ref(term, n.label_id(), pos))

        try:
            cfr_part = node.label[0]
        except IndexError:
            cfr_part = None

        if settings.INCLUDE_DEFINITIONS_IN.get(cfr_part):
            for included_term, context in settings.INCLUDE_DEFINITIONS_IN[
                    cfr_part]:
                if context in node.text and included_term in node.text:
                    pos_start = node.text.index(included_term)
                    add_match(node, included_term.lower(),
                              (pos_start, pos_start + len(included_term)))

        if stack and self.has_parent_definitions_indicator(stack):
            for match, _, _ in grammar.smart_quotes.scanString(node.text):
                term = match.term.tokens[0].lower().strip(',.;')
                #   Don't use pos_end because we are stripping some chars
                pos_start = match.term.pos[0]
                add_match(node,
                          term,
                          (pos_start, pos_start + len(term)))

        for match, _, _ in grammar.scope_term_type_parser.scanString(
                node.text):
            # Check that both scope and term look valid
            if (self.scope_of_text(match.scope, Label.from_node(node),
                                   verify_prefix=False)
                    and re.match("^[a-z ]+$", match.term.tokens[0])):
                term = match.term.tokens[0].strip()
                pos_start = node.text.index(term, match.term.pos[0])
                add_match(node, term, (pos_start, pos_start + len(term)))

        if hasattr(node, 'tagged_text'):
            for match, _, _ in grammar.xml_term_parser.scanString(
                    node.tagged_text):
                """Position in match reflects XML tags, so its dropped in
                preference of new values based on node.text."""
                for match in chain([match.head], match.tail):
                    pos_start = self.pos_start_excluding(
                        match.term.tokens[0], node.text,
                        included_defs + excluded_defs)
                    term = node.tagged_text[
                        match.term.pos[0]:match.term.pos[1]].lower()
                    match_len = len(term)
                    add_match(node,
                              term,
                              (pos_start, pos_start + match_len))

        return included_defs, excluded_defs

    def pos_start_excluding(self, needle, haystack, exclusions):
        """Search for the first instance of `needle` in the `haystack`
        excluding any overlaps from `exclusions`. Implicitly returns None if
        it can't be found"""
        # TODO: This cannot under any circumstances return None because it's
        #       being used in an addition upstack.
        start = 0
        while start >= 0:
            start = haystack.find(needle, start)
            if not any(r.position[0] <= start and r.position[1] >= start
                       for r in exclusions):
                return start
            start += 1

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
        exclusions = self.per_regulation_ignores(
            exclusions, node.label, node.text)

        inclusions = self.included_offsets(node.label_id(), node.text)
        inclusions = self.per_regulation_includes(
            inclusions, node.label, node.text)

        matches = self.calculate_offsets(node.text, term_list, exclusions)
        for term, ref, offsets in matches:
            layer_el.append({
                "ref": ref.term + ':' + ref.label,
                "offsets": offsets
                })
        return layer_el

    def per_regulation_ignores(self, exclusions, label, text):
        cfr_part = label[0]
        if settings.IGNORE_DEFINITIONS_IN.get(cfr_part):
            for ignore_term in settings.IGNORE_DEFINITIONS_IN[cfr_part]:
                exclusions.extend(
                    (match.start(), match.end()) for match in
                    re.finditer(r'\b' + re.escape(ignore_term) + r'\b', text))
        return exclusions

    def excluded_offsets(self, label, text):
        """We explicitly exclude certain chunks of text (for example, words
        we are defining shouldn't have links appear within the defined
        term.) More will be added in the future"""
        exclusions = []
        for reflist in self.scoped_terms.values():
            exclusions.extend(
                ref.position for ref in reflist if ref.label == label)
        for ignore_term in settings.IGNORE_DEFINITIONS_IN['ALL']:
            exclusions.extend(
                (match.start(), match.end()) for match in
                re.finditer(r'\b' + re.escape(ignore_term) + r'\b', text))
        return exclusions

    def per_regulation_includes(self, inclusions, label, text):
        cfr_part = label[0]
        if settings.INCLUDE_DEFINITIONS_IN.get(cfr_part):
            for included_term, context in settings.INCLUDE_DEFINITIONS_IN[
                    'ALL']:
                inclusions.extend(
                    (match.start(), match.end()) for match in
                    re.finditer(
                        r'\b' + re.escape(included_term) + r'\b', text))
        return inclusions

    def included_offsets(self, label, text):
        """ We explicitly include certain chunks of text (for example,
            words that the parser doesn't necessarily pick up as being
            defined) that should be part of a defined term """
        inclusions = []
        for included_term, context in settings.INCLUDE_DEFINITIONS_IN['ALL']:
            inclusions.extend(
                (match.start(), match.end()) for match in
                re.finditer(r'\b' + re.escape(included_term) + r'\b', text))
        return inclusions

    def calculate_offsets(self, text, applicable_terms, exclusions=[],
                          inclusions=[]):
        """Search for defined terms in this text, with a preference for all
        larger (i.e. containing) terms."""

        # don't modify the original
        exclusions = list(exclusions)
        inclusions = list(inclusions)

        # add plurals to applicable terms
        pluralized = [(inflection.pluralize(t[0]), t[1])
                      for t in applicable_terms]
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

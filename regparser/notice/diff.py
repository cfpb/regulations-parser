# vim: set encoding=utf-8
from itertools import takewhile
import re
from copy import copy

from lxml import etree

from regparser.grammar import amdpar, tokens
from regparser.tree.struct import Node
from regparser.tree.xml_parser.reg_text import build_from_section
from regparser.tree.xml_parser.tree_utils import get_node_text


def clear_between(xml_node, start_char, end_char):
    """Gets rid of any content (including xml nodes) between chars"""
    as_str = etree.tostring(xml_node, encoding=unicode)
    start_char, end_char = re.escape(start_char), re.escape(end_char)
    pattern = re.compile(
        start_char + '[^' + end_char + ']*' + end_char, re.M + re.S + re.U)
    return etree.fromstring(pattern.sub('', as_str))


def remove_char(xml_node, char):
    """Remove from this node and all its children"""
    as_str = etree.tostring(xml_node, encoding=unicode)
    return etree.fromstring(as_str.replace(char, ''))


def fix_section_node(paragraphs, amdpar_xml):
    """ When notices are corrected, the XML for notices doesn't follow the
    normal syntax. Namely, pargraphs aren't inside section tags. We fix that
    here, by finding the preceding section tag and appending paragraphs to it.
    """

    sections = [s for s in amdpar_xml.itersiblings(preceding=True)
                if s.tag == 'SECTION']

    # Let's only do this if we find one section tag.
    if len(sections) == 1:
        section = copy(sections[0])
        for paragraph in paragraphs:
            section.append(copy(paragraph))
        return section


def find_lost_section(amdpar_xml):
    """ This amdpar doesn't have any following siblings, so we
    look in the next regtext """
    reg_text = amdpar_xml.getparent()
    reg_text_siblings = [s for s in reg_text.itersiblings()
                         if s.tag == 'REGTEXT']
    if len(reg_text_siblings) > 0:
        candidate_reg_text = reg_text_siblings[0]
        amdpars = [a for a in candidate_reg_text if a.tag == 'AMDPAR']
        if len(amdpars) == 0:
            # Only do this if there are not AMDPARS
            for c in candidate_reg_text:
                if c.tag == 'SECTION':
                    return c


def find_section(amdpar_xml):
    """ With an AMDPAR xml, return the first section
    sibling """
    siblings = [s for s in amdpar_xml.itersiblings()]

    if len(siblings) == 0:
        return find_lost_section(amdpar_xml)

    section = None
    for sibling in amdpar_xml.itersiblings():
        if sibling.tag == 'SECTION':
            section = sibling

    if section is None:
        paragraphs = [s for s in amdpar_xml.itersiblings() if s.tag == 'P']
        if len(paragraphs) > 0:
            return fix_section_node(paragraphs, amdpar_xml)
    return section


def find_subpart(amdpar_tag):
    """ Look amongst an amdpar tag's siblings to find a subpart. """
    for sibling in amdpar_tag.itersiblings():
        if sibling.tag == 'SUBPART':
            return sibling


def find_diffs(xml_tree, cfr_part):
    """Find the XML nodes that are needed to determine diffs"""
    #   Only final notices have this format
    for section in xml_tree.xpath('//REGTEXT//SECTION'):
        section = clear_between(section, '[', ']')
        section = remove_char(remove_char(section, u'▸'), u'◂')
        for node in build_from_section(cfr_part, section):
            def per_node(node):
                if node_is_empty(node):
                    for c in node.children:
                        per_node(c)
            per_node(node)


def node_is_empty(node):
    """Handle different ways the regulation represents no content"""
    return node.text.strip() == ''


def switch_context(token_list, carried_context):
    """ Notices can refer to multiple regulations (CFR parts). If the
    CFR part changes, empty out the context that we carry forward. """

    def is_valid_label(label):
        return label and label[0] is not None

    if carried_context and carried_context[0] is not None:
        token_list = [t for t in token_list if hasattr(t, 'label')]
        reg_parts = [t.label[0] for t in token_list if is_valid_label(t.label)]

        if len(reg_parts) > 0:
            reg_part = reg_parts[0]
            if reg_part != carried_context[0]:
                return []
    return carried_context


def contains_one_instance(tokenized, element):
    """ Return True if tokenized contains only one instance of the class
    element. """
    contexts = [t for t in tokenized if isinstance(t, element)]
    return len(contexts) == 1


def contains_one_paragraph(tokenized):
    """ Returns True if tokenized contains only one tokens.Paragraph """
    return contains_one_instance(tokenized, tokens.Paragraph)


def contains_delete(tokenized):
    """ Returns True if tokenized contains at least one DELETE. """
    contexts = [t for t in tokenized if t.match(tokens.Verb, verb='DELETE')]
    return len(contexts) > 0


def remove_false_deletes(tokenized, text):
    """ Sometimes a statement like 'Removing the 'x' from the end of
    paragraph can be confused as removing the paragraph. Ensure that
    doesn't happen here. Likely this method needs a little more work. """

    if contains_delete(tokenized):
        if contains_one_paragraph(tokenized):
            if 'end of paragraph' in text:
                return []
    return tokenized


def paragraph_in_context_moved(tokenized, initial_context):
    """Catches this situation: "Paragraph 1 under subheading 51(b)(1) is
    redesignated as paragraph 7 under subheading 51(b)", i.e. a Paragraph
    within a Context moved to another Paragraph within a Context. The
    contexts and paragraphs in this situation need to be swapped."""
    final_tokens = []
    idx = 0
    while idx < len(tokenized) - 4:
        par1, cont1, verb, par2, cont2 = tokenized[idx:idx + 5]
        if (par1.match(tokens.Paragraph) and cont1.match(tokens.Context)
                and verb.match(tokens.Verb, verb=tokens.Verb.MOVE,
                               active=False)
                and par2.match(tokens.Paragraph)
                and cont2.match(tokens.Context)
                and all(tok.label[1:2] == ['Interpretations']
                        for tok in (par1, cont1, par2, cont2))):
            batch, initial_context = compress_context(
                [cont1, par1, verb, cont2, par2], initial_context)
            final_tokens.extend(batch)
            idx += 5
        else:
            final_tokens.append(tokenized[idx])
            idx += 1
    final_tokens.extend(tokenized[idx:])
    return final_tokens


def move_then_modify(tokenized):
    """The subject of modification may be implicit in the preceding move
    operation: A is redesignated B and changed. Replace the operation with a
    DELETE and a POST so it's easier to compile later."""
    final_tokens = []
    idx = 0
    while idx < len(tokenized) - 3:
        move, p1, p2, edit = tokenized[idx:idx + 4]
        if (move.match(tokens.Verb, verb=tokens.Verb.MOVE, active=True)
                and p1.match(tokens.Paragraph)
                and p2.match(tokens.Paragraph)
                and edit.match(tokens.Verb, verb=tokens.Verb.PUT,
                               active=True, and_prefix=True)):
            final_tokens.append(tokens.Verb(tokens.Verb.DELETE, active=True))
            final_tokens.append(p1)
            final_tokens.append(tokens.Verb(tokens.Verb.POST, active=True))
            final_tokens.append(p2)
            idx += 4
        else:
            final_tokens.append(tokenized[idx])
            idx += 1
    final_tokens.extend(tokenized[idx:])
    return final_tokens


def parse_amdpar(par, initial_context):
    """ Parse the <AMDPAR> tags into a list of paragraphs that have changed.
    """

    #   Replace and "and"s in titles; they will throw off and_token_resolution
    for e in filter(lambda e: e.text, par.xpath('./E')):
        e.text = e.text.replace(' and ', ' ')
    text = get_node_text(par, add_spaces=True)
    tokenized = [t[0] for t, _, _ in amdpar.token_patterns.scanString(text)]

    tokenized = compress_context_in_tokenlists(tokenized)
    tokenized = resolve_confused_context(tokenized, initial_context)
    tokenized = paragraph_in_context_moved(tokenized, initial_context)
    tokenized = remove_false_deletes(tokenized, text)
    tokenized = multiple_moves(tokenized)
    tokenized = switch_passive(tokenized)
    tokenized = and_token_resolution(tokenized)
    tokenized, subpart = deal_with_subpart_adds(tokenized)
    tokenized = context_to_paragraph(tokenized)
    tokenized = move_then_modify(tokenized)
    if not subpart:
        tokenized = separate_tokenlist(tokenized)
    initial_context = switch_context(tokenized, initial_context)
    tokenized, final_context = compress_context(tokenized, initial_context)
    amends = make_amendments(tokenized, subpart)
    return amends, final_context


def multiple_moves(tokenized):
    """Phrases like paragraphs 1 and 2 are redesignated paragraphs 3 and 4
    are replaced with Move(active), paragraph 1, paragraph 3, Move(active)
    paragraph 2, paragraph 4"""
    converted = []
    skip = 0
    for idx, el0 in enumerate(tokenized):
        if skip:
            skip -= 1
        elif idx < len(tokenized) - 2:
            el1, el2 = tokenized[idx+1:idx+3]
            if (el0.match(tokens.TokenList) and el2.match(tokens.TokenList)
                    and el1.match(tokens.Verb, verb=tokens.Verb.MOVE,
                                  active=False)
                    and len(el0.tokens) == len(el2.tokens)):
                skip = 2
                for tidx in range(len(el0.tokens)):
                    converted.append(el1.copy(active=True))
                    converted.append(el0.tokens[tidx])
                    converted.append(el2.tokens[tidx])
            else:
                converted.append(el0)
        else:
            converted.append(el0)
    return converted


def switch_passive(tokenized):
    """Passive verbs are modifying the phrase before them rather than the
    phrase following. For consistency, we flip the order of such verbs"""
    if all(not t.match(tokens.Verb, active=False) for t in tokenized):
        return tokenized
    converted, remaining = [], tokenized
    while remaining:
        to_add = list(takewhile(
            lambda t: not isinstance(t, tokens.Verb), remaining))
        if len(to_add) < len(remaining):
            #   also take the verb
            verb = remaining[len(to_add)].copy()
            to_add.append(verb)
            #   switch verb to the beginning
            if not verb.active:
                to_add = to_add[-1:] + to_add[:-1]
                verb.active = True
                #   may need to grab one more if the verb is move
                if (verb.verb == tokens.Verb.MOVE
                        and len(to_add) < len(remaining)):
                    to_add.append(remaining[len(to_add)])
        converted.extend(to_add)
        remaining = remaining[len(to_add):]
    return converted


def resolve_confused_context(tokenized, initial_context):
    """Resolve situation where a Context thinks it is regtext, but it
    *should* be an interpretation"""
    if initial_context[1:2] == ['Interpretations']:
        final_tokens = []
        for token in tokenized:
            if (token.match(tokens.Context, tokens.Paragraph)
                    and len(token.label) > 1 and token.label[1] is None):
                final_tokens.append(token.copy(
                    label=[token.label[0], 'Interpretations', token.label[2],
                           '(' + ')('.join(l for l in token.label[3:] if l)
                           + ')']))
            elif (token.match(tokens.Context, tokens.Paragraph)
                    and len(token.label) > 1 and
                    token.label[1].startswith('Appendix:')):
                final_tokens.append(token.copy(
                    label=[token.label[0], 'Interpretations',
                           token.label[1][len('Appendix:'):],
                           '(' + ')('.join(l for l in token.label[2:] if l)
                           + ')']))
            elif token.match(tokens.TokenList):
                sub_tokens = resolve_confused_context(token.tokens,
                                                      initial_context)
                final_tokens.append(token.copy(tokens=sub_tokens))
            else:
                final_tokens.append(token)
        return final_tokens
    else:
        return tokenized


def and_token_resolution(tokenized):
    """Troublesome case where a Context should be a Paragraph, but the only
    indicator is the presence of an "and" token afterwards. We'll likely
    want to expand this step in the future, but for now, we only catch a few
    cases"""
    # compress "and" tokens
    tokenized = zip(tokenized, tokenized[1:] + [None])
    tokenized = [l for l, r in tokenized
                 if l != r or not l.match(tokens.AndToken)]

    # we'll strip out all "and" tokens in just a moment, but as a first
    # pass, remove all those preceded by a verb (which makes the following
    # logic simpler).
    tokenized = list(reversed(tokenized))
    tokenized = zip(tokenized, tokenized[1:] + [None])
    tokenized = list(reversed([l for l, r in tokenized
                               if not l.match(tokens.AndToken) or not r
                               or not r.match(tokens.Verb)]))

    # check for the pattern in question
    final_tokens = []
    idx = 0
    while idx < len(tokenized) - 3:
        t1, t2, t3, t4 = tokenized[idx:idx + 4]
        if (t1.match(tokens.Verb) and t2.match(tokens.Context)
                and t3.match(tokens.AndToken)
                and t4.match(tokens.Paragraph, tokens.TokenList)):
            final_tokens.append(t1)
            final_tokens.append(tokens.Paragraph(t2.label))
            final_tokens.append(t4)
            idx += 3    # not 4 as one will appear below
        elif t1 != tokens.AndToken:
            final_tokens.append(t1)
        idx += 1

    final_tokens.extend(tokenized[idx:])
    return final_tokens


def context_to_paragraph(tokenized):
    """Generally, section numbers, subparts, etc. are good contextual clues,
    but sometimes they are the object of manipulation."""

    #   Don't modify anything if there are already paragraphs or no verbs
    for token in tokenized:
        if isinstance(token, tokens.Paragraph):
            return tokenized
        elif (isinstance(token, tokens.TokenList) and
                any(isinstance(t, tokens.Paragraph) for t in token.tokens)):
            return tokenized
    # copy
    converted = list(tokenized)
    verb_seen = False
    for i in range(len(converted)):
        token = converted[i]
        if isinstance(token, tokens.Verb):
            verb_seen = True
        elif verb_seen and token.match(tokens.Context, certain=False):
            converted[i] = tokens.Paragraph(token.label)
    return converted


def is_designate_token(token):
    """ This is a designate token """
    return token.match(tokens.Verb, verb=tokens.Verb.DESIGNATE)


def contains_one_designate_token(tokenized):
    """ Return True if the list of tokens contains only one designate token.
    """
    designate_tokens = [t for t in tokenized if is_designate_token(t)]
    return len(designate_tokens) == 1


def contains_one_tokenlist(tokenized):
    """ Return True if the list of tokens contains only one TokenList """
    tokens_lists = [t for t in tokenized if isinstance(t, tokens.TokenList)]
    return len(tokens_lists) == 1


def contains_one_context(tokenized):
    """ Returns True if the list of tokens contains only one Context. """
    contexts = [t for t in tokenized if isinstance(t, tokens.Context)]
    return len(contexts) == 1


def deal_with_subpart_adds(tokenized):
    """If we have a designate verb, and a token list, we're going to
    change the context to a Paragraph. Because it's not a context, it's
    part of the manipulation."""

    # Ensure that we only have one of each: designate verb, a token list and
    # a context
    verb_exists = contains_one_designate_token(tokenized)
    list_exists = contains_one_tokenlist(tokenized)
    context_exists = contains_one_context(tokenized)

    if verb_exists and list_exists and context_exists:
        token_list = []
        for token in tokenized:
            if isinstance(token, tokens.Context):
                token_list.append(tokens.Paragraph(token.label))
            else:
                token_list.append(token)
        return token_list, True
    else:
        return tokenized, False


def separate_tokenlist(tokenized):
    """When we come across a token list, separate it out into individual
    tokens"""

    converted = []
    for token in tokenized:
        if isinstance(token, tokens.TokenList):
            converted.extend(token.tokens)
        else:
            converted.append(token)
    return converted


def compress(lhs_label, rhs_label):
    """Combine two labels where the rhs replaces the lhs. If the rhs is
    empty, assume the lhs takes precedent."""
    if not rhs_label:
        return lhs_label

    label = list(lhs_label)
    label.extend([None]*len(rhs_label))
    label = label[:len(rhs_label)]

    for i in range(len(rhs_label)):
        label[i] = rhs_label[i] or label[i]
    return label


def compress_context_in_tokenlists(tokenized):
    """Use compress (above) on elements within a tokenlist."""
    final = []
    for token in tokenized:
        if token.match(tokens.TokenList):
            subtokens = []
            label_so_far = []
            for subtoken in token.tokens:
                if hasattr(subtoken, 'label'):
                    label_so_far = compress(label_so_far, subtoken.label)
                    subtokens.append(subtoken.copy(label=label_so_far))
                else:
                    subtokens.append(subtoken)
            final.append(token.copy(tokens=subtokens))
        else:
            final.append(token)
    return final


def compress_context(tokenized, initial_context):
    """Add context to each of the paragraphs (removing context)"""
    # copy
    context = list(initial_context)
    converted = []
    for token in tokenized:
        if isinstance(token, tokens.Context):
            # Interpretations of appendices
            if (len(context) > 1 and len(token.label) > 1
                    and context[1] == 'Interpretations'
                    and (token.label[1] or '').startswith('Appendix')):
                context = compress(
                    context,
                    [token.label[0], None, token.label[1]] + token.label[2:])
            else:
                context = compress(context, token.label)
            continue
        #   Another corner case: a "paragraph" is indicates interp context
        elif (
            isinstance(token, tokens.Paragraph) and len(context) > 1
            and len(token.label) > 3 and context[1] == 'Interpretations'
                and token.label[1] != 'Interpretations'):
            context = compress(
                context,
                [token.label[0], None, token.label[2], '(' + ')('.join(
                    p for p in token.label[3:] if p) + ')'])
            continue
        elif isinstance(token, tokens.Paragraph):
            context = compress(context, token.label)
            token.label = context
        converted.append(token)
    return converted, context


def get_destination(tokenized, reg_part):
    """ In a designate scenario, get the destination label.  """

    paragraphs = [t for t in tokenized if isinstance(t, tokens.Paragraph)]
    destination = paragraphs[0]

    if destination.label[0] is None:
        # Sometimes the destination label doesn't know the reg part.
        destination.label[0] = reg_part

    destination = destination.label_text()
    return destination


def handle_subpart_amendment(tokenized):
    """ Handle the situation where a new subpart is designated. """
    verb = tokens.Verb.DESIGNATE

    token_lists = [t for t in tokenized if isinstance(t, tokens.TokenList)]

    # There's only one token list of paragraphs, sections to be designated
    tokens_to_be_designated = token_lists[0]
    labels_to_be_designated = [t.label_text() for t in tokens_to_be_designated]
    reg_part = tokens_to_be_designated.tokens[0].label[0]
    destination = get_destination(tokenized, reg_part)

    return DesignateAmendment(verb, labels_to_be_designated, destination)


class Amendment(object):
    """ An Amendment object contains all the information necessary for
    an amendment. """

    TITLE = '[title]'
    TEXT = '[text]'
    HEADING = '[heading]'

    def remove_intro(self, l):
        """ Remove the marker that indicates this is a change to introductory
        text. """
        l = l.replace(self.TITLE, '').replace(self.TEXT, '')
        return l.replace(self.HEADING, '')

    def fix_interp_format(self, components):
        """Convert between the interp format of amendments and the normal,
        node label format"""
        if ['Interpretations'] == components[1:2]:
            if len(components) > 2:
                new_style = [components[0],
                             components[2].replace('Appendix:', '')]
                # Add paragraphs
                if len(components) > 3:
                    paragraphs = [p.strip('()')
                                  for p in components[3].split(')(')]
                    paragraphs = filter(bool, paragraphs)
                    new_style.extend(paragraphs)
                new_style.append(Node.INTERP_MARK)
                # Add any paragraphs of the comment
                new_style.extend(components[4:])
                return new_style
            else:
                return components[:1] + [Node.INTERP_MARK]
        return components

    def fix_appendix_format(self, components):
        """Convert between the appendix format of amendments and the normal,
        node label format"""
        return [c.replace('Appendix:', '') for c in components]

    def fix_label(self, label):
        """ The labels that come back from parsing the list of amendments
        are not the same type we use in the rest of parsing. Convert between
        the two here (removing question markers, converting to interp
        format, etc.)"""
        def wanted(l):
            return l != '?' and 'Subpart' not in l

        components = label.split('-')
        components = [self.remove_intro(l) for l in components if wanted(l)]
        components = self.fix_interp_format(components)
        components = self.fix_appendix_format(components)
        return components

    def __init__(self, action, label, destination=None):
        self.action = action
        self.original_label = label
        self.label = self.fix_label(self.original_label)

        if destination and '-' in destination:
            self.destination = self.fix_interp_format(destination.split('-'))
        else:
            self.destination = destination

        if self.TITLE in self.original_label:
            self.field = self.TITLE
        elif self.TEXT in self.original_label:
            self.field = self.TEXT
        elif self.HEADING in self.original_label:
            self.field = self.HEADING
        else:
            self.field = None

    def label_id(self):
        """ Return the label id (dash delimited) for this label. """
        return '-'.join(self.label)

    def __repr__(self):
        if self.destination:
            return '(%s, %s, %s)' % (self.action, self.label, self.destination)
        else:
            return '(%s, %s)' % (self.action, self.label)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)


class DesignateAmendment(Amendment):
    """ A designate Amendment manages it's information a little differently
    than a normal Amendment. Namely, there's more handling around Subparts."""

    def __init__(self, action, label_list, destination):
        self.action = action
        self.original_labels = label_list
        self.labels = [self.fix_label(l) for l in self.original_labels]
        self.original_destination = destination

        if 'Subpart' in destination and ':' in destination:
            reg_part, subpart = self.original_destination.split('-')
            _, subpart_letter = destination.split(':')
            self.destination = [reg_part, 'Subpart', subpart_letter]
        elif '-' in destination:
            self.destination = self.fix_interp_format(destination.split('-'))
        else:
            self.destination = destination

    def __repr__(self):
        return "(%s, %s, %s)" % (
            repr(self.action), repr(self.labels), repr(self.destination))


def make_amendments(tokenized, subpart=False):
    """Convert a sequence of (normalized) tokens into a list of amendments"""
    verb = None
    amends = []
    if subpart:
        amends.append(handle_subpart_amendment(tokenized))
    else:
        for i in range(len(tokenized)):
            token = tokenized[i]
            if isinstance(token, tokens.Verb):
                assert token.active
                verb = token.verb
            elif isinstance(token, tokens.Paragraph):
                if verb == tokens.Verb.MOVE:
                    if isinstance(tokenized[i-1], tokens.Paragraph):
                        origin = tokenized[i-1].label_text()
                        destination = token.label_text()
                        amends.append(Amendment(verb, origin, destination))
                elif verb:
                    amends.append(Amendment(verb, token.label_text()))
    # Edits to intro text should always be PUTs
    for amend in amends:
        if (not isinstance(amend, DesignateAmendment)
                and amend.field == "[text]"
                and amend.action == tokens.Verb.POST):
            amend.action = tokens.Verb.PUT
    return amends


def new_subpart_added(amendment):
    """ Return True if label indicates that a new subpart was added """
    new_subpart = amendment.action == 'POST'
    label = amendment.original_label
    m = [t for t, _, _ in amdpar.subpart_label.scanString(label)]
    return (len(m) > 0 and new_subpart)

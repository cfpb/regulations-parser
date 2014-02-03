#vim: set encoding=utf-8
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

    #Let's only do this if we find one section tag.
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
            #Only do this if there are not AMDPARS
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
                else:
                    print node.label, node.text
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
        token_list = [t for t in token_list if not isinstance(t, tokens.Verb)]
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
    contexts = [t for t in tokenized
                if isinstance(t, tokens.Verb) and t.verb == 'DELETE']
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


def parse_amdpar(par, initial_context):
    """ Parse the <AMDPAR> tags into a list of paragraphs that have changed.
    """

    text = get_node_text(par, add_spaces=True)
    tokenized = [t[0] for t, _, _ in amdpar.token_patterns.scanString(text)]

    tokenized = remove_false_deletes(tokenized, text)
    tokenized = multiple_moves(tokenized)
    tokenized = switch_passive(tokenized)
    tokenized, subpart = deal_with_subpart_adds(tokenized)
    tokenized = context_to_paragraph(tokenized)
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
            if (isinstance(el0, tokens.TokenList)
                    and isinstance(el1, tokens.Verb) and not el1.active
                    and el1.verb == tokens.Verb.MOVE
                    and isinstance(el2, tokens.TokenList)
                    and len(el0.tokens) == len(el2.tokens)):
                skip = 2
                for tidx in range(len(el0.tokens)):
                    converted.append(tokens.Verb(tokens.Verb.MOVE, True))
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
    if all(not isinstance(t, tokens.Verb) or t.active for t in tokenized):
        return tokenized
    converted, remaining = [], tokenized
    while remaining:
        to_add = list(takewhile(
            lambda t: not isinstance(t, tokens.Verb), remaining))
        if len(to_add) < len(remaining):
            #   also take the verb
            verb = remaining[len(to_add)]
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
    #copy
    converted = list(tokenized)
    verb_seen = False
    for i in range(len(converted)):
        token = converted[i]
        if isinstance(token, tokens.Verb):
            verb_seen = True
        elif (verb_seen and isinstance(token, tokens.Context)
                and not token.certain):
            converted[i] = tokens.Paragraph(token.label)
    return converted


def is_designate_token(token):
    """ This is a designate token """
    designate = tokens.Verb.DESIGNATE
    return isinstance(token, tokens.Verb) and token.verb == designate


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

    #Ensure that we only have one of each: designate verb, a token list and
    #a context
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


def compress_context(tokenized, initial_context):
    """Add context to each of the paragraphs (removing context)"""
    #copy
    context = list(initial_context)
    converted = []
    for token in tokenized:
        if isinstance(token, tokens.Context):
            #   One corner case: interpretations of appendices
            if (len(context) > 1 and len(token.label) > 1
                and context[1] == 'Interpretations'
                    and token.label[1]
                    and token.label[1].startswith('Appendix')):
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
        #Sometimes the destination label doesn't know the reg part.
        destination.label[0] = reg_part

    destination = destination.label_text()
    return destination


def handle_subpart_amendment(tokenized):
    """ Handle the situation where a new subpart is designated. """

    verb = tokens.Verb.DESIGNATE

    token_lists = [t for t in tokenized if isinstance(t, tokens.TokenList)]

    #There's only one token list of paragraphs, sections to be designated
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
        if ['Interpretations'] == components[1:2] and len(components) > 2:
            new_style = [components[0], components[2].replace('Appendix:', '')]
            # Add paragraphs
            if len(components) > 3:
                paragraphs = [p.strip('()') for p in components[3].split(')(')]
                new_style.extend(paragraphs)
            new_style.append(Node.INTERP_MARK)
            # Add any paragraphs of the comment
            new_style.extend(components[4:])
            return new_style
        return components

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
    return amends


def new_subpart_added(amendment):
    """ Return True if label indicates that a new subpart was added. """

    new_subpart = amendment.action == 'POST'
    label = amendment.original_label
    m = [t for t, _, _ in amdpar.subpart_label.scanString(label)]
    return len(m) > 0 and new_subpart

#vim: set encoding=utf-8
from itertools import takewhile
import re

from lxml import etree

from regparser.grammar import amdpar, tokens
from regparser.tree import struct
from regparser.tree.xml_parser.reg_text import build_from_section


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


def find_diffs(xml_tree, cfr_part):
    """Find the XML nodes that are needed to determine diffs"""
    last_context = []
    diffs = []
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


def parse_amdpar(par, initial_context):
    text = etree.tostring(par, encoding=unicode)
    #print ""
    #print text.strip()
    tokenized = [t[0] for t, _, _ in amdpar.token_patterns.scanString(text)]
    tokenized = switch_passive(tokenized)
    tokenized = context_to_paragraph(tokenized)
    tokenized = separate_tokenlist(tokenized)
    tokenized, final_context = compress_context(tokenized, initial_context)
    amends = make_amendments(tokenized)
    return amends, final_context


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
            #also take the verb
            verb = remaining[len(to_add)]
            to_add.append(verb)
            if not verb.active:
                #switch it to the beginning
                to_add = to_add[-1:] + to_add[:-1]
                verb.active = True
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


def make_amendments(tokenized):
    """Convert a sequence of (normalized) tokens into a list of amendments"""
    verb = None
    amends = []
    for i in range(len(tokenized)):
        token = tokenized[i]

        if isinstance(token, tokens.Verb):
            assert token.active
            verb = token.verb
        elif isinstance(token, tokens.Paragraph):
            if verb == tokens.Verb.MOVE:
                if isinstance(tokenized[i-1], tokens.Paragraph):
                    amends.append((
                        verb,
                        (tokenized[i-1].label_text(), token.label_text())))
            elif verb:
                amends.append((verb, token.label_text()))
    return amends

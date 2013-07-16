#vim: set encoding=utf-8
import re

from lxml import etree

from regparser.grammar import rules as grammar, tokens
from regparser.tree import struct
from regparser.tree.xml_parser.reg_text import build_section

def clear_between(xml_node, start_char, end_char):
    """Gets rid of any content (including xml nodes) between chars"""
    as_str = etree.tostring(xml_node, encoding=unicode)
    start_char, end_char = re.escape(start_char), re.escape(end_char)
    pattern = re.compile(start_char + '[^' + end_char + ']*' + end_char, 
            re.M + re.S + re.U)
    return etree.fromstring(pattern.sub('', as_str))


def remove_char(xml_node, char):
    """Remove from this node and all its children"""
    as_str = etree.tostring(xml_node, encoding=unicode)
    return etree.fromstring(as_str.replace(char, ''))
    

def find_diffs(xml_tree):
    """Find the XML nodes that are needed to determine diffs"""
    last_context = None
    diffs = []
    #   Only final notices have this format
    for section in xml_tree.xpath('//REGTEXT//SECTION'):
        section = clear_between(section, '[', ']')
        section = remove_char(remove_char(section, u'▸'), u'◂')
        node = build_section('1005', section)
        if node:
            def per_node(node):
                if node_is_empty(node):
                    for c in node['children']:
                        per_node(c)
                else:
                    print node['label']['parts'], node['text']
            per_node(node)

def node_is_empty(node):
    """Handle different ways the regulation represents no content"""
    return node['text'].strip() == ''

def parse_amdpar(par, initial_context):
    text = etree.tostring(par, encoding=unicode)
    print ""
    print text.strip()
    tokenized = [t[0] for t,s,e in grammar.amdpar_tokens.scanString(text)]
    simplified = simplify_tokens(tokenized)
    diffs, final_context = tokens_to_diffs(simplified, initial_context)
    for diff in diffs:
        print diff
    return final_context

def simplify_tokens(tokenized):
    simplified = list(tokenized)    #   copy
    for i in range(len(tokenized)):
        if (i < len(tokenized) - 1 
                and isinstance(tokenized[i], tokens.SectionHeadingOf)):
            simplified[i] = tokenized[i+1]
            simplified[i+1] = tokens.SectionHeading()
        if (i > 0 and isinstance(tokenized[i], tokens.Verb)
                and not tokenized[i].active):
            simplified[i] = tokenized[i-1]
            simplified[i-1] = tokens.Verb(tokenized[i].verb, True)
    return simplified


def tokens_to_diffs(tokenized, initial_context):
    context = initial_context
    verb = None
    diffs = []
    for i in range(len(tokenized)):
        token = tokenized[i]
        if isinstance(token, tokens.Verb):
            verb = token.verb
        elif isinstance(token, tokens.Section):
            context = [token.part, token.section]
        elif isinstance(token, tokens.Paragraph):
            p_id = token.id(context)

            if verb == 'MOVE': 
                if isinstance(tokenized[i-1], tokens.Paragraph):
                    diffs.append((verb, '-'.join(context), '-'.join(p_id)))
            else:
                if token.text:
                    modifier = '[text]'
                else:
                    modifier = ''
                diffs.append((verb, '-'.join(p_id) + modifier))

            context = p_id
        elif isinstance(token, tokens.ParagraphList):
            for p in token.paragraphs:
                p_id = p.id(context)
                context = p_id
                if p.text:
                    modifier = '[text]'
                else:
                    modifier = ''

                diffs.append((verb, '-'.join(context) + modifier))
        elif isinstance(token, tokens.SectionHeading):
            diffs.append((verb, '-'.join(context) + '[title]'))
        elif isinstance(token, tokens.IntroText):
            diffs.append((verb, '-'.join(context) + '[text]'))
        elif isinstance(token, tokens.Appendix):
            p_id = token.id(context)
            context = p_id
            diffs.append((verb, '-'.join(context)))
        elif isinstance(token, tokens.AppendixList):
            for a in token.appendices:
                p_id = a.id(context)
                context = p_id
                diffs.append((verb, '-'.join(context)))
    return diffs, context


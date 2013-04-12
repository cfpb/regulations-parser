#vim: set encoding=utf-8
import string
from grammar import internal_citations as grammar
from pyparsing import Word, Optional, oneOf, OneOrMore, Regex, originalTextFor, Suppress

class InternalCitationParser(object):

    def parse(self, text, parts=None):
        """ Parse the provided text, pulling out all the internal (self-referential) 
        citations. """

        c = originalTextFor(grammar.any_citation)
        all_citations = []

        def build_layer_element(token, start, end, prefix=[]):
            return {
                'offsets': [[start, end]],
                'citation': prefix + token.asList()
            }

        for citation, start, end in grammar.any_citation.scanString(text):
            if citation.single_paragraph or citation.multiple_paragraphs:
                paragraph_citation_prefix = parts[0:2]
                for t, s, e in grammar.depth1_p.scanString(text):
                    if s >= start and e <= end:
                        all_citations.append(build_layer_element(t, s, e, paragraph_citation_prefix))
            elif citation.multiple_sections:
                for t, s, e in grammar.single_section.scanString(text):
                    all_citations.append(build_layer_element(t, s, e))
            else:
                all_citations.append(build_layer_element(citation, start, end))
        return all_citations

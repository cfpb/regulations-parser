#vim: set encoding=utf-8
import string
import urllib
from collections import defaultdict
from parser.grammar import external_citations as grammar

from layer import Layer

class ExternalCitationParser(Layer):
    #The different types of citations
    CODE_OF_FEDERAL_REGULATIONS = 'CFR'
    UNITED_STATES_CODE = 'USC'
    THE_ACT = 'ACT'
    PUBLIC_LAW = 'PUBLIC_LAW'

    def citation_type(self, citation):
        """ Based on the citation parsed, return the type of the citation. """
        if citation[1] == 'CFR':
            return ExternalCitationParser.CODE_OF_FEDERAL_REGULATIONS
        elif citation[1] == 'U.S.C.':
            return ExternalCitationParser.UNITED_STATES_CODE
        elif 'Act' in citation:
            return ExternalCitationParser.THE_ACT
        elif 'Public' in citation and 'Law' in citation:
            return ExternalCitationParser.PUBLIC_LAW

    def reformat_citation(self, citation):
        """ Strip out unnecessary elements from the citation reference, so that 
        the various types of citations are presented consistently. """
        return [c for c in citation if c not in ['U.S.C.', 'CFR', 'part', '.', 'Public', 'Law', '-']]

    def parse(self, text, parts=None):
        """ Parse the provided text, pulling out all the citations. """
        parser  = grammar.regtext_external_citation

        cm = defaultdict(list)
        citation_strings = {}
        for citation, start, end in parser.scanString(text):
            index = "-".join(citation)
            cm[index].append([start, end])
            citation_strings[index] = citation.asList()

        def build_layer_element(k, offsets):
            layer_element = {'offsets': offsets, 
                'citation': self.reformat_citation(citation_strings[k]),
                'citation_type': self.citation_type(citation_strings[k])
            }
            return layer_element

        return  [build_layer_element(k, offsets) for k,offsets in cm.items()]

    def process(self, node):
        citations_list = self.parse(node['text'], parts=node['label']['parts'])
        if citations_list:
            return citations_list

#vim: set encoding=utf-8
from collections import defaultdict
from regparser.grammar import external_citations as grammar
import string
import urllib

from layer import Layer

class ExternalCitationParser(Layer):
    #The different types of citations
    CODE_OF_FEDERAL_REGULATIONS = 'CFR'
    UNITED_STATES_CODE = 'USC'
    PUBLIC_LAW = 'PUBLIC_LAW'
    STATUTES_AT_LARGE = 'STATUTES_AT_LARGE'

    def __init__(self, tree, act_citation):
        Layer.__init__(self, tree)
        self.act_citation = act_citation

    def citation_type(self, citation):
        """ Based on the citation parsed, return the type of the citation. """
        if citation[1] == 'CFR':
            return ExternalCitationParser.CODE_OF_FEDERAL_REGULATIONS
        elif citation[1] == 'U.S.C.' or 'Act' in citation:
            return ExternalCitationParser.UNITED_STATES_CODE
        elif 'Public' in citation and 'Law' in citation:
            return ExternalCitationParser.PUBLIC_LAW
        elif 'Stat.' in citation:
            return ExternalCitationParser.STATUTES_AT_LARGE

    def reformat_citation(self, citation):
        """ Strip out unnecessary elements from the citation reference, so that 
        the various types of citations are presented consistently. """
        if 'Act' in citation:
            citation = self.act_citation
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
        citations_list = self.parse(node.text, parts=node.label)
        if citations_list:
            return citations_list

#vim: set encoding=utf-8
import string
import urllib
from collections import defaultdict
from pyparsing import *

class ExternalCitationParser(object):
    #The different types of citations
    CODE_OF_FEDERAL_REGULATIONS = 'CFR'
    UNITED_STATES_CODE = 'USC'

    def get_parser(self):
        """ Construct a grammar that parses references/citations to the 
        United States Code and the Code of Federal Regulations. """
        uscode_exp = Word(string.digits) + "U.S.C." + Word(string.digits)

        cfr_exp_v1 = Word(string.digits) + "CFR" + "part" + Word(string.digits)
        cfr_exp_v2 = Word(string.digits) + "CFR" + Word(string.digits) + "." + Word(string.digits)
        cfr_exp = cfr_exp_v1.setResultsName('V1') ^ cfr_exp_v2.setResultsName('V2')

        parse_all =  uscode_exp.setResultsName('USC') | cfr_exp
        return parse_all

    def citation_type(self, citation):
        """ Based on the citation parsed, return the type of the citation. """
        if citation[1] == 'CFR':
            return ExternalCitationParser.CODE_OF_FEDERAL_REGULATIONS
        elif citation[1] == 'U.S.C.':
            return ExternalCitationParser.UNITED_STATES_CODE

    def reformat_citation(self, citation):
        """ Strip out unnecessary elements from the citation reference, so that 
        the various types of citations are presented consistently. """
        return [c for c in citation if c not in ['U.S.C.', 'CFR', 'part', '.']]

    def parse(self, text):
        """ Parse the provided text, pulling out all the citations. """
        parser  = self.get_parser()

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

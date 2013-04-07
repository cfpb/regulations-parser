#vim: set encoding=utf-8
import string
from pyparsing import Word, Optional, oneOf, OneOrMore, Regex, originalTextFor, Suppress

class InternalCitationGrammar(object):
    """ Define the grammar to parse internal citations in the text of a United
    States regulation. """

    def __init__(self):
        self.lower_alpha_sub = Suppress("(") + Word(string.ascii_lowercase).setResultsName("id") + Suppress(")")
        self.upper_alpha_sub = Suppress("(") + Word(string.ascii_uppercase).setResultsName("id") + Suppress(")")
        self.roman_sub = Suppress("(") + Word("ivxlcdm").setResultsName("id") + Suppress(")")
        self.digit_sub = Suppress("(") + Word(string.digits).setResultsName("id") + Suppress(")")

    def get_sub_sub_paragraph_grammar(self):
        sub_sub_paragraph = (
                self.lower_alpha_sub.setResultsName("level1") + 
                Optional(self.digit_sub.setResultsName("level2") +
                Optional(self.roman_sub.setResultsName("level3") + 
                Optional(self.upper_alpha_sub.setResultsName("level4"))))
        )
        return sub_sub_paragraph

    def get_single_section_grammar(self):
        sub_sub_paragraph = self.get_sub_sub_paragraph_grammar()

        single_section = (Word(string.digits) + "." + Word(string.digits) +
            Optional(sub_sub_paragraph) + Optional(Regex(",|and") + OneOrMore(
            self.lower_alpha_sub | self.upper_alpha_sub | self.roman_sub | self.digit_sub)))

        return single_section

    def get_multiple_section_citation_grammar(self):
        single_section = self.get_single_section_grammar()

        multiple_section_citation = (u"§§" + single_section + OneOrMore(
            Regex(",|and") + Optional("and") + single_section))
        return multiple_section_citation

    def single_paragraph_grammar(self):
        sub_sub_paragraph = self.get_sub_sub_paragraph_grammar()
        single_paragraph = "paragraph" + sub_sub_paragraph
        return single_paragraph

    def multiple_paragraph_grammar(self):
        sub_sub_paragraph = self.get_sub_sub_paragraph_grammar()
        multiple_paragraphs = (
                "paragraphs" + 
                sub_sub_paragraph.setResultsName("car") + 
                OneOrMore(
                    Regex(",|and") + Optional("and") + 
                    sub_sub_paragraph.setResultsName("cdr", listAllMatches=True)
                )
            )
        return multiple_paragraphs

    def any_citation_grammar(self):
        multiple_section_citation = self.get_multiple_section_citation_grammar()
        single_section_citation =  self.get_single_section_grammar()
        single_paragraph = self.single_paragraph_grammar()
        multiple_paragraphs =  self.multiple_paragraph_grammar()

        any_citation = (multiple_section_citation | single_section_citation
                | single_paragraph | multiple_paragraphs)
        return any_citation

class InternalCitationParser(object):

    def __init__(self):
        self.citation_grammar = InternalCitationGrammar()

    def parse(self, text, parts=None):
        """ Parse the provided text, pulling out all the internal (self-referential) 
        citations. """

        parser = self.citation_grammar.any_citation_grammar()
        sub_sub_paragraph = self.citation_grammar.get_sub_sub_paragraph_grammar()
        c = originalTextFor(parser)
        all_citations = []

        for citation, start, end in parser.scanString(text):
            for t,s,e in c.scanString(text):
                if s == start and e == end:
                    original_text = t[0]

            if citation[0] == 'paragraphs' or citation[0] == 'paragraph':
                #print '++++++++++'
                paragraph_citation_prefix = parts[0:2]
                #print text.encode('utf-8', 'ignore')
                #print original_text
                #print (start, end)
                for t, s, e in sub_sub_paragraph.scanString(text):
                    layer_element = {'offsets': [[s, e]],
                        'citation': paragraph_citation_prefix + t.asList()
                    }
                    all_citations.append(layer_element)
                    #print layer_element
                #print '-----------'
            return all_citations
            #elif citation[0] == u"§§":  
            #    single_section_parser =  self.citation_grammar.get_single_section_grammar()
            #    for t, s, e in single_section_parser.scanString(original_text):
            #        print text
            #        print original_text
            #        print (start, end)
            #        layer_element = {
            #            'offsets': [[s, e]],
            #            'citation':t.asList()
            #        }
            #        print layer_element

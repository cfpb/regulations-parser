#vim: set encoding=utf-8
import string
from pyparsing import Word, Optional, oneOf, OneOrMore, Regex, originalTextFor

class InternalCitationGrammar(object):
    def __init__(self):
        self.lower_alpha_sub = "(" + Word(string.ascii_lowercase).setResultsName("id") + ")"
        self.upper_alpha_sub = "(" + Word(string.ascii_uppercase).setResultsName("id") + ")"
        self.roman_sub = "(" + Word("ivxlcdm").setResultsName("id") + ")"
        self.digit_sub = "(" + Word(string.digits).setResultsName("id") + ")"

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
        any_citation = (multiple_section_citation | single_section_citation
                | single_paragraph | multiple_paragraphs)
        return any_citation


class InternalCitationParser(object):

    def get_parser(self):
        lower_alpha_sub = "(" + Word(string.ascii_lowercase).setResultsName("id") + ")"
        upper_alpha_sub = "(" + Word(string.ascii_uppercase).setResultsName("id") + ")"
        roman_sub = "(" + Word("ivxlcdm").setResultsName("id") + ")"
        digit_sub = "(" + Word(string.digits).setResultsName("id") + ")"

        sub_sub_paragraph = (
                lower_alpha_sub.setResultsName("level1") + 
                Optional(digit_sub.setResultsName("level2") +
                Optional(roman_sub.setResultsName("level3") + 
                Optional(upper_alpha_sub.setResultsName("level4"))))
        )

        single_section = (Word(string.digits) + "." + Word(string.digits) +
                Optional(sub_sub_paragraph) + Optional(Regex(",|and") + OneOrMore(
                    lower_alpha_sub | upper_alpha_sub | roman_sub | digit_sub)))

        multiple_section_citation = (u"§§" + single_section + OneOrMore(
            Regex(",|and") + Optional("and") + single_section))

        single_section_citation = (u"§" + single_section)

        single_paragraph = "paragraph" + sub_sub_paragraph
        multiple_paragraphs = (
            "paragraphs" + 
            sub_sub_paragraph.setResultsName("car") + 
            OneOrMore(
                Regex(",|and") + Optional("and") + 
                sub_sub_paragraph.setResultsName("cdr", listAllMatches=True)
            )
        )

        any_citation = (multiple_section_citation | single_section_citation
                | single_paragraph | multiple_paragraphs)

        return any_citation

    def parse(self, text):
        """ Parse the provided text, pulling out all the internal (self-referential) 
        citations. """

        parser = self.get_parser()

        for citation, start, end in parser.scanString(text):
            if citation[0] == 'paragraphs':
                c = originalTextFor(parser)
                for m, s, e in c.scanString(text):
                    print m
                    print (s, e)

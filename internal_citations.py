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
                sections = [citation.s_head] + list(citation.s_tail)
                for section in sections:
                    all_citations.extend(self.single_section(section,
                        section.pos[0], section.pos[1]))
            else:
                all_citations.extend(self.single_section(
                    citation.without_marker, start, end))
        return self.strip_whitespace(text, all_citations)

    def strip_whitespace(self, text, citations):
        """Modifies the offsets to exclude any trailing whitespace. Modifies
        the offsets in place."""
        for citation in citations:
            for i in range(len(citation['offsets'])):
                start, end = citation['offsets'][i]
                string = text[start:end]
                lstring = string.lstrip()
                rstring = string.rstrip()
                new_start = start + (len(string) - len(lstring))
                new_end = end - (len(string) - len(rstring))
                citation['offsets'][i] = (new_start, new_end)
        return citations



    def single_section(self, match, start, end):
        """Return the layer elements associated with a single section
        reference."""
        citations = []
        label = [match.part, match.section]
        if match.p_head:
            label.append(match.p_head.level1)
            label.append(match.p_head.level2)
            label.append(match.p_head.level3)
            label.append(match.p_head.level4)
            end = match.p_head.pos[1]
        else:
            label.extend([None, None, None, None])
        citations.append({
            'offsets': [(match.pos[0] ,end)], 
            'citation': filter(bool, label)
            })
        for el in match.p_tail:
            p = el.p
            if p.level1:
                label[2:6] = [p.level1, p.level2, p.level3, p.level4]
            elif p.level2:
                label[3:6] = [p.level2, p.level3, p.level4]
            elif p.level3:
                label[4:6] = [p.level3, p.level4]
            else:
                label[5] = p.level5
            citations.append({
                'offsets': [p.pos], 
                'citation': filter(bool, label)
                })
        return citations

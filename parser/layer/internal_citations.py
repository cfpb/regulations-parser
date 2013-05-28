#vim: set encoding=utf-8
import string
from parser.grammar import internal_citations as grammar

from layer import Layer

class InternalCitationParser(Layer):

    def parse(self, text, parts=None):
        """ Parse the provided text, pulling out all the internal (self-referential) 
        citations. """

        all_citations = []

        for citation, start, end in grammar.regtext_citation.scanString(text):
            if citation.single_paragraph or citation.multiple_paragraphs:
                if citation.single_paragraph:
                    citation = citation.single_paragraph
                else:
                    citation = citation.multiple_paragraphs
                all_citations.extend(self.paragraph_list(citation, 
                    citation.p_head.pos[0], end, parts[0], parts[1]))
            elif citation.multiple_sections:
                sections = [citation.s_head] + list(citation.s_tail)
                for section in sections:
                    all_citations.extend(self.paragraph_list(section,
                        section.pos[0], section.pos[1], section.part, 
                        section.section))
            else:
                citation = citation.without_marker
                all_citations.extend(self.paragraph_list(citation, 
                    citation.pos[0], end, citation.part, 
                    citation.section))

        for cit, start, end in grammar.appendix_citation.scanString(text):
            cit = cit[0][0]
            label = [parts[0], cit.appendix, cit.section]
            if cit.paragraphs:
                label += list(cit.paragraphs[0][0])
            all_citations.append({
                "offsets": [cit.pos],
                "citation": label
            })

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

    def paragraph_list(self, match, start, end, part, section):
        """Return the layer elements associated with a list of paragraphs.
        Use the part/section as the prefix for the citation's list."""
        citations = []
        label = [part, section]
        if match.p_head:
            label.append(match.p_head.level1)
            label.append(match.p_head.level2)
            label.append(match.p_head.level3)
            label.append(match.p_head.level4)
            end = match.p_head.pos[1]
        else:
            label.extend([None, None, None, None])
        citations.append({
            'offsets': [(start,end)], 
            'citation': filter(bool, label)
            })
        for p in match.p_tail:
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

    def process(self, node):
        citations_list = self.parse(node['text'], parts=node['label']['parts'])
        if citations_list:
            return citations_list

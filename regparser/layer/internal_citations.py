#vim: set encoding=utf-8
import re
import string

from regparser.grammar import internal_citations as grammar
from regparser.layer.layer import Layer

class InternalCitationParser(Layer):

    def parse(self, text, parts=None):
        """ Parse the provided text, pulling out all the internal (self-referential) 
        citations. """

        all_citations = self.regtext_citations(text, parts)
        all_citations.extend(self.comment_citations(text, parts))

        for cit, start, end in grammar.appendix_citation.scanString(text):
            label = [parts[0], cit.appendix, cit.section]
            all_citations.extend(self.paragraph_list(cit, start, end,
                label))

        return self.strip_whitespace(text, all_citations)

    def regtext_citations(self, text, parts):
        """Find all citations that refer to regtext"""
        citations = []
        #   If referring to a specific paragraph using regtext notation, we
        #   are not discussing an interp paragraph; use the associated regtext
        paragraph_parts = [p for p in parts if p != 'Interpretations']
        if len(paragraph_parts) < parts:    # Was an interp
            #   Remember to strip out any specific paragraph info
            paragraph_parts[1] = re.sub(r'\(.+\)', '', paragraph_parts[1])
            
        for citation, start, end in grammar.regtext_citation.scanString(text):
            if citation.single_paragraph or citation.multiple_paragraphs:
                if citation.single_paragraph:
                    citation = citation.single_paragraph
                else:
                    citation = citation.multiple_paragraphs
                citations.extend(self.paragraph_list(citation, 
                    citation.p_head.pos[0], end, paragraph_parts[0:2]))
            elif citation.multiple_sections:
                sections = [citation.s_head] + list(citation.s_tail)
                for section in sections:
                    citations.extend(self.paragraph_list(section,
                        section.pos[0], section.pos[1], 
                        [section.part, section.section]))
            else:
                citation = citation.without_marker
                citations.extend(self.paragraph_list(citation, 
                    citation.pos[0], end, 
                    [citation.part, citation.section]))
        return citations

    def comment_citations(self, text, parts):
        """Find all citations that refer to interpretations"""
        citations = []
        for cit, start, end in grammar.comment_citation.scanString(text):
            label = [parts[0], 'Interpretations']
            if cit.multiple_comments:
                comments = [cit.c_head] + list(cit.c_tail)
            else:
                comments = [cit.without_marker]
            for comment in comments:
                start, end = comment.pos
                cit = comment.tokens
                label = [parts[0], 'Interpretations']
                paragraph_ref = ')('.join(filter(bool, list(cit.p_head)))
                label.append(cit.section + '(' + paragraph_ref + ')')
                label.append(cit.level1)
                label.append(cit.level2)
                label.append(cit.level3)
                citations.append({
                    'offsets': [(start, end)],
                    'citation': filter(bool, label)
                })
        return citations

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

    def paragraph_list(self, match, start, end, label):
        """Return the layer elements associated with a list of paragraphs.
        Use the part/section as the prefix for the citation's list."""
        citations = []
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
                label[-4:] = [p.level1, p.level2, p.level3, p.level4]
            elif p.level2:
                label[-3:] = [p.level2, p.level3, p.level4]
            elif p.level3:
                label[-2:] = [p.level3, p.level4]
            else:
                label[-1] = p.level4
            citations.append({
                'offsets': [p.pos], 
                'citation': filter(bool, label)
                })
        return citations

    def process(self, node):
        citations_list = self.parse(node['text'], parts=node['label']['parts'])
        if citations_list:
            return citations_list

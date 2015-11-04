# vim: set encoding=utf-8
import logging

from regparser.citations import internal_citations, Label
from regparser.layer.layer import Layer
from regparser.tree.struct import walk


class InternalCitationParser(Layer):
    def __init__(self, *args, **kwargs):
        Layer.__init__(self, *args, **kwargs)
        self.known_citations = set()
        self.verify_citations = True

    def pre_process(self):
        """As a preprocessing step, run through the entire tree, collecting
        all labels."""
        def per_node(node):
            self.known_citations.add(tuple(node.label))
        walk(self.tree, per_node)

    def process(self, node):
        citations_list = self.parse(node.text,
                                    label=Label.from_node(node),
                                    title=str(self.cfr_title))
        if citations_list:
            return citations_list

    def remove_missing_citations(self, citations, text):
        """Remove any citations to labels we have not seen before (i.e.
        those collected in the pre_processing stage)"""
        final = []
        for c in citations:
            if tuple(c.label.to_list()) in self.known_citations:
                final.append(c)
            else:
                logging.warning("Missing citation? %s %r"
                                % (text[c.start:c.end], c.label))
        return final

    def parse(self, text, label, title=None):
        """ Parse the provided text, pulling out all the internal
        (self-referential) citations. """

        to_layer = lambda pc: {'offsets': [(pc.start, pc.end)],
                               'citation': pc.label.to_list()}
        citations = internal_citations(text, label,
                                       require_marker=True, title=title)
        if self.verify_citations:
            citations = self.remove_missing_citations(citations, text)
        all_citations = list(map(to_layer, citations))

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

#vim: set encoding=utf-8
from itertools import takewhile
import re
import string

from regparser.citations import internal_citations, Label
from regparser.layer.layer import Layer
from regparser.tree.struct import Node


class InternalCitationParser(Layer):

    def process(self, node):
        citations_list = self.parse(node.text, label=Label.from_node(node))
        if citations_list:
            return citations_list

    def parse(self, text, label):
        """ Parse the provided text, pulling out all the internal
        (self-referential) citations. """

        to_layer = lambda pc: {'offsets': [(pc.start, pc.end)],
                               'citation': pc.label.to_list()}
        all_citations = list(map(to_layer,
            internal_citations(text, label, require_marker=True)))

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


# vim: set encoding=utf-8
from unittest import TestCase

from regparser.layer import external_citations
from regparser.tree.struct import Node


class ParseTest(TestCase):

    def test_section_act(self):
        """
            Test an external reference that looks like this: "section 918 of
            the Act"
        """
        node = Node('section 918 of the Act', label=['1005', '2'])
        parser = external_citations.ExternalCitationParser(
            None, act_citation=['1234', '5678'])
        citations = parser.process(node)

        self.assertEqual(len(citations), 1)

        citation = citations[0]
        self.assertEqual(citation['citation'], ['1234', '5678'])
        self.assertEqual(citation['citation_type'], 'USC')
        self.assertEqual(citation['offsets'][0][0], 15)

    def test_public_law(self):
        """
            Ensure that we successfully parse Public Law citations that look
            like the following: Public Law 111-203
        """
        node = Node("Public Law 111-203", label=['1005', '2'])
        parser = external_citations.ExternalCitationParser(None)
        citations = parser.process(node)
        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0]['citation_type'], 'PUBLIC_LAW')

    def test_statues_at_large(self):
        """
            Ensure that we successfully parse Statues at Large citations that
            look like the following: 122 Stat. 1375
        """
        node = Node('122 Stat. 1375', label=['1003', '5'])
        parser = external_citations.ExternalCitationParser(None)
        citations = parser.process(node)
        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0]['citation_type'], 'STATUTES_AT_LARGE')

    def test_cfr(self):
        """Ensure that we successfully parse CFR references."""
        node = Node("Ref 1: 12 CFR part 1026. "
                    + "Ref 2: 12 CFR 1026.13.")
        parser = external_citations.ExternalCitationParser(None)
        citations = parser.process(node)
        self.assertEqual(2, len(citations))
        self.assertEqual("CFR", citations[0]['citation_type'])
        self.assertEqual("CFR", citations[1]['citation_type'])

    def test_drop_self_referential_cfr(self):
        """
            Ensure that CFR references that refer to the reg being parsed are
            not marked as external citations.
        """
        node = Node("11 CFR 110.14", label=['110', '1'])
        parser = external_citations.ExternalCitationParser(None)
        parser.cfr_title = '11'
        citations = parser.process(node)
        self.assertEqual(None, citations)

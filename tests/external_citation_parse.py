#vim: set encoding=utf-8
from unittest import TestCase
from parser.layer import external_citations

class ParseTest(TestCase):

    def test_section_act(self):
        """
            Test an external reference that looks like this: "section 918 of the Act"
        """
        node = {'text': u"section 918 of the Act", 'label':{'parts':[1005, 2]}}
        parser = external_citations.ExternalCitationParser(None)
        citations = parser.process(node)

        self.assertEqual(len(citations), 1)

        citation = citations[0]
        self.assertEqual(citation['citation'], ['the', 'Act'])
        self.assertEqual(citation['offsets'][0][0], 15)

    def test_public_law(self):
        """
            Ensure that we successfully parse Public Law citations that look like 
            the following: Public Law 111-203
        """
        node = {'text': u"Public Law 111-203", 'label':{'parts':[1005, 2]}}
        parser = external_citations.ExternalCitationParser(None)
        citations = parser.process(node)
        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0]['citation_type'], 'PUBLIC_LAW')

    def test_statues_at_large(self):
        """
            Ensure that we successfully parse Statues at Large citations that look 
            like the following: 122 Stat. 1375
        """
        node = {'text': u'122 Stat. 1375', 'label':{'parts':[1003, 5]}}
        parser = external_citations.ExternalCitationParser(None)
        citations = parser.process(node)
        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0]['citation_type'], 'STATUES_AT_LARGE')

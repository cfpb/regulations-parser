#vim: set encoding=utf-8
from unittest import TestCase
from parser.layer import external_citations

class ParseTest(TestCase):

    def test_section_act(self):
        """
            Test an external reference that looks like this: "section 918 of the Act"
        """
        text = u"section 918 of the Act"
        parser = external_citations.ExternalCitationParser()
        citations = parser.parse(text, parts=None)

        self.assertEqual(len(citations), 1)

        citation = citations[0]
        self.assertEqual(citation['citation'], ['the', 'Act'])
        self.assertEqual(citation['offsets'][0][0], 15)

    def test_public_law(self):
        """
            Ensure that we successfully parse Public Law citations that look like 
            the following: Public Law 111-203
        """
        text = u"Public Law 111-203"
        parser = external_citations.ExternalCitationParser()
        citations = parser.parse(text, parts=None)

        self.assertEqual(len(citations), 1)
        print citations

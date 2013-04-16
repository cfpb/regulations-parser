#vim: set encoding=utf-8
from unittest import TestCase
import external_citations


class ParseTest(TestCase):
    def test_section_act(self):
        """
            Test an external reference that looks like this: "section 918 of the Act"
        """
        text = u"section 918 of the Act"
        parser = external_citations.ExternalCitationParser()
        citations = parser.parse(text, parts=None)

        for c in citations:
            print c
        self.assertEqual(True, False)

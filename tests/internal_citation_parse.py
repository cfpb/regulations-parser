from unittest import TestCase
import internal_citations

class ParseTest(TestCase):

    def test_multiple_paragraphs(self):

        parser = internal_citations.InternalCitationParser()
        text = u"the requirements of paragraphs (c)(3), (d)(2), (e)(1), (e)(3), and (f) of this section"
        citations = parser.parse(text, parts = ['1005', '6'])

        for c in citations:
            if c['citation'] == ['1005', '6', u'c', u'3']:
                self.assertEqual(text[c['offsets'][0][0]], '(')
                self.assertEquals(c['offsets'], [[31, 37]])
                self.assertEquals(text[c['offsets'][0][0] + 1], 'c')
            if c['citation'] == ['1005', '6', u'd', u'2']:
                self.assertEquals(text[c['offsets'][0][0] + 1], 'd')

    def test_single_paragraph(self):
        parser = internal_citations.InternalCitationParser()
        text = 'The requirements in paragraph (a)(4)(iii) of'
        citations = parser.parse(text, parts = ['1005', '6'])
        c = citations[0]
        self.assertEquals(text[c['offsets'][0][0]:c['offsets'][0][1] - 1], u'(a)(4)(iii)')

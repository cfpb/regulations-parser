# vim: set encoding=utf-8
from unittest import TestCase

from regparser.layer import internal_citations
from regparser.tree.struct import Node


class ParseTest(TestCase):
    def setUp(self):
        self.parser = internal_citations.InternalCitationParser(None)
        self.parser.verify_citations = False

    def test_process_method(self):
        node = Node("The requirements in paragraph (a)(4)(iii) of",
                    label=['1005', '6'])
        citations = self.parser.process(node)
        self.assertEqual(len(citations), 1)

    def test_underparagraph(self):
        text = 'Something something underparagraphs (a)(4) through (5)'
        citations = self.parser.process(Node(text, label=['1005', '6']))
        self.assertEqual(len(citations), 2)

    def test_except_for(self):
        text = 'paragraph (b)(2)(i) through (b)(2)(v) except for '
        text += '(b)(2)(i)(D) and (b)(2)(vii) through (b)(2)(xiv)'
        citations = self.parser.process(Node(text, label=['1005', '6']))
        self.assertEqual(len(citations), 5)
        self.assertEqual(citations[0]['citation'],
                         ['1005', '6', 'b', '2', 'i'])
        self.assertEqual(citations[1]['citation'],
                         ['1005', '6', 'b', '2', 'v'])
        self.assertEqual(citations[2]['citation'],
                         ['1005', '6', 'b', '2', 'i', 'D'])
        self.assertEqual(citations[3]['citation'],
                         ['1005', '6', 'b', '2', 'vii'])
        self.assertEqual(citations[4]['citation'],
                         ['1005', '6', 'b', '2', 'xiv'])

        text = 'paragraph (b)(2)(i) through (b)(2)(v) (except for '
        text += '(b)(2)(i)(D)) and (b)(2)(vii) through (b)(2)(xiv)'
        citations = self.parser.process(Node(text, label=['1005', '6']))
        self.assertEqual(len(citations), 5)
        self.assertEqual(citations[0]['citation'],
                         ['1005', '6', 'b', '2', 'i'])
        self.assertEqual(citations[1]['citation'],
                         ['1005', '6', 'b', '2', 'v'])
        self.assertEqual(citations[2]['citation'],
                         ['1005', '6', 'b', '2', 'i', 'D'])
        self.assertEqual(citations[3]['citation'],
                         ['1005', '6', 'b', '2', 'vii'])
        self.assertEqual(citations[4]['citation'],
                         ['1005', '6', 'b', '2', 'xiv'])

    def test_multiple_paragraphs(self):
        """ Ensure that offsets work correctly in a simple multiple paragraph
        scenario. """

        text = u"the requirements of paragraphs (c)(3), (d)(2), (e)(1), "
        text += "(e)(3), and (f) of this section"
        citations = self.parser.process(Node(text, label=['1005', '6']))

        self.assertEqual(len(citations), 5)

        for c in citations:
            if c['citation'] == ['1005', '6', u'c', u'3']:
                self.assertEqual(text[c['offsets'][0][0]], '(')
                self.assertEquals(c['offsets'], [(31, 37)])
                self.assertEquals(text[c['offsets'][0][0] + 1], 'c')
            if c['citation'] == ['1005', '6', u'd', u'2']:
                self.assertEquals(text[c['offsets'][0][0] + 1], 'd')

    def test_multiple_paragraph_or(self):
        """ Ensure that an 'or' between internal citations is matched
        correctly. """
        text = u"set forth in paragraphs (b)(1) or (b)(2)"
        citations = self.parser.process(Node(text, label=['1005', '6']))
        self.assertEquals(2, len(citations))

    def test_single_paragraph(self):
        """ Ensure that offsets work correctly in a simple single paragraph
        citation. """
        text = 'The requirements in paragraph (a)(4)(iii) of'
        citations = self.parser.process(Node(text, label=['1005', '6']))
        c = citations[0]
        self.assertEquals(text[c['offsets'][0][0]:c['offsets'][0][1]],
                          u'(a)(4)(iii)')
        self.assertEquals(['1005', '6', 'a', '4', 'iii'], c['citation'])

    def test_single_labeled_paragraph(self):
        """ Ensure the parser doesn't pick up unecessary elements, such as the
        (a) in the text below. """
        text = '(a) Solicited issuance. Except as provided in paragraph (b) '
        text += 'of this section'
        citations = self.parser.process(Node(text, label=['1005', '6']))
        self.assertEqual(1, len(citations))

    def test_multiple_section_citation(self):
        """ Ensure that offsets work correctly in a simple multiple section
        citation case. """
        text = u"set forth in §§ 1005.6(b)(3) and 1005.11 (b)(1)(i) from 60 "
        text += "days"
        citations = self.parser.process(Node(text, label=['1005', '6']))

        self.assertEqual(len(citations), 2)
        occurrences = 0
        for c in citations:
            if c['citation'] == [u'1005', u'6', u'b', u'3']:
                occurrences += 1
                self.assertEquals(text[c['offsets'][0][0]:c['offsets'][0][1]],
                                  u'1005.6(b)(3)')
            if c['citation'] == [u'1005', u'11', u'b', u'1', u'i']:
                occurrences += 1
                self.assertEquals(text[c['offsets'][0][0]:c['offsets'][0][1]],
                                  u'1005.11 (b)(1)(i)')
        self.assertEquals(occurrences, 2)

    def test_single_section_citation(self):
        """ Ensure that offsets work correctly in a simple single section
        citation case. """
        text = u"date in § 1005.20(h)(1) must disclose"
        citations = self.parser.process(Node(text, label=['1005', '6']))
        c = citations[0]
        self.assertEquals(text[c['offsets'][0][0]:c['offsets'][0][1]],
                          u'1005.20(h)(1)')

    def test_multiple_paragraph_single_section(self):
        text = u'§ 1005.10(a) and (d)'
        result = self.parser.process(Node(text, label=['1005', '6']))
        self.assertEqual(2, len(result))
        self.assertEqual(['1005', '10', 'a'], result[0]['citation'])
        self.assertEqual(['1005', '10', 'd'], result[1]['citation'])
        start, end = result[0]['offsets'][0]
        self.assertEqual(u'1005.10(a)', text[start:end])
        start, end = result[1]['offsets'][0]
        self.assertEqual(u'(d)', text[start:end])

    def test_multiple_paragraph_single_section2(self):
        text = u'§ 1005.7(b)(1), (2) and (3)'
        result = self.parser.process(Node(text, label=['1005', '6']))
        self.assertEqual(3, len(result))
        self.assertEqual(['1005', '7', 'b', '1'], result[0]['citation'])
        self.assertEqual(['1005', '7', 'b', '2'], result[1]['citation'])
        self.assertEqual(['1005', '7', 'b', '3'], result[2]['citation'])
        start, end = result[0]['offsets'][0]
        self.assertEqual(u'1005.7(b)(1)', text[start:end])
        start, end = result[1]['offsets'][0]
        self.assertEqual(u'(2)', text[start:end])
        start, end = result[2]['offsets'][0]
        self.assertEqual(u'(3)', text[start:end])

    def test_multiple_paragraphs_this_section(self):
        text = u'paragraphs (c)(1) and (2) of this section'
        result = self.parser.process(Node(text, label=['1005', '6']))
        self.assertEqual(2, len(result))
        self.assertEqual(['1005', '6', 'c', '1'], result[0]['citation'])
        self.assertEqual(['1005', '6', 'c', '2'], result[1]['citation'])
        start, end = result[0]['offsets'][0]
        self.assertEqual(u'(c)(1)', text[start:end])
        start, end = result[1]['offsets'][0]
        self.assertEqual(u'(2)', text[start:end])

    def test_multiple_paragraphs_alpha_then_roman1(self):
        text = u'paragraphs (b)(1)(ii) and (iii)'
        result = self.parser.process(Node(text, label=['1005', '6']))
        self.assertEqual(2, len(result))
        self.assertEqual(['1005', '6', 'b', '1', 'ii'], result[0]['citation'])
        self.assertEqual(['1005', '6', 'b', '1', 'iii'], result[1]['citation'])
        start, end = result[0]['offsets'][0]
        self.assertEqual(u'(b)(1)(ii)', text[start:end])
        start, end = result[1]['offsets'][0]
        self.assertEqual(u'(iii)', text[start:end])

    def test_multiple_paragraphs_max_depth(self):
        text = u'see paragraphs (z)(9)(vi)(A) and (D)'
        results = self.parser.process(Node(text, label=['999', '88']))
        self.assertEqual(2, len(results))
        resultA, resultD = results
        self.assertEqual(['999', '88', 'z', '9', 'vi', 'A'],
                         resultA['citation'])
        offsets = resultA['offsets'][0]
        self.assertEqual('(z)(9)(vi)(A)', text[offsets[0]:offsets[1]])
        self.assertEqual(['999', '88', 'z', '9', 'vi', 'D'],
                         resultD['citation'])
        offsets = resultD['offsets'][0]
        self.assertEqual('(D)', text[offsets[0]:offsets[1]])

    def test_multiple_paragraphs_alpha_then_roman2(self):
        text = u'§ 1005.15(d)(1)(i) and (ii)'
        result = self.parser.process(Node(text, label=['1005', '15']))
        self.assertEqual(2, len(result))
        self.assertEqual(['1005', '15', 'd', '1', 'i'], result[0]['citation'])
        self.assertEqual(['1005', '15', 'd', '1', 'ii'], result[1]['citation'])
        start, end = result[0]['offsets'][0]
        self.assertEqual(u'1005.15(d)(1)(i)', text[start:end])
        start, end = result[1]['offsets'][0]
        self.assertEqual(u'(ii)', text[start:end])

    def test_multiple_paragraphs_alpha_then_roman3(self):
        text = u'§ 1005.9(a)(5) (i), (ii), or (iii)'
        result = self.parser.process(Node(text, label=['1005', '9']))
        self.assertEqual(3, len(result))
        self.assertEqual(['1005', '9', 'a', '5', 'i'], result[0]['citation'])
        self.assertEqual(['1005', '9', 'a', '5', 'ii'], result[1]['citation'])
        self.assertEqual(['1005', '9', 'a', '5', 'iii'], result[2]['citation'])
        start, end = result[0]['offsets'][0]
        self.assertEqual(u'1005.9(a)(5) (i)', text[start:end])
        start, end = result[1]['offsets'][0]
        self.assertEqual(u'(ii)', text[start:end])
        start, end = result[2]['offsets'][0]
        self.assertEqual(u'(iii)', text[start:end])

    def test_multiple_paragraphs_alpha_then_roman4(self):
        text = u'§ 1005.11(a)(1)(vi) or (vii).'
        result = self.parser.process(Node(text, label=['1005', '11']))
        self.assertEqual(2, len(result))
        self.assertEqual(['1005', '11', 'a', '1', 'vi'], result[0]['citation'])
        self.assertEqual(['1005', '11', 'a', '1', 'vii'],
                         result[1]['citation'])
        start, end = result[0]['offsets'][0]
        self.assertEqual(u'1005.11(a)(1)(vi)', text[start:end])
        start, end = result[1]['offsets'][0]
        self.assertEqual(u'(vii)', text[start:end])

    def test_appendix_citation(self):
        text = "Please see A-5 and Q-2(r) and Z-12(g)(2)(ii) then more text"
        result = self.parser.process(Node(text, label=['1005', '10']))
        self.assertEqual(3, len(result))
        resultA, resultQ, resultZ = result

        self.assertEqual(['1005', 'A', '5'], resultA['citation'])
        offsets = resultA['offsets'][0]
        self.assertEqual('A-5', text[offsets[0]:offsets[1]])
        self.assertEqual(['1005', 'Q', '2(r)'], resultQ['citation'])
        offsets = resultQ['offsets'][0]
        self.assertEqual('Q-2(r)', text[offsets[0]:offsets[1]])
        self.assertEqual(['1005', 'Z', '12(g)(2)(ii)'], resultZ['citation'])
        offsets = resultZ['offsets'][0]
        self.assertEqual('Z-12(g)(2)(ii)', text[offsets[0]:offsets[1]])

    def test_section_verbose(self):
        text = "And Section 222.87(d)(2)(i) says something"
        result = self.parser.process(Node(text, label=['222', '87']))
        self.assertEqual(1, len(result))
        self.assertEqual(['222', '87', 'd', '2', 'i'], result[0]['citation'])
        offsets = result[0]['offsets'][0]
        self.assertEqual('222.87(d)(2)(i)', text[offsets[0]:offsets[1]])

    def test_sections_verbose(self):
        text = "Listing sections 11.55(d) and 321.11 (h)(4)"
        result = self.parser.process(Node(text, label=['222', '87']))
        self.assertEqual(2, len(result))
        r11, r321 = result

        self.assertEqual(['11', '55', 'd'], r11['citation'])
        offsets = r11['offsets'][0]
        self.assertEqual('11.55(d)', text[offsets[0]:offsets[1]])

        self.assertEqual(['321', '11', 'h', '4'], r321['citation'])
        offsets = r321['offsets'][0]
        self.assertEqual('321.11 (h)(4)', text[offsets[0]:offsets[1]])

    def test_comment_header(self):
        text = "See comment 32(b)(3) blah blah"
        result = self.parser.process(Node(text, label=['222', '87']))
        self.assertEqual(1, len(result))
        self.assertEqual(['222', '32', 'b', '3', Node.INTERP_MARK],
                         result[0]['citation'])
        offsets = result[0]['offsets'][0]
        self.assertEqual('32(b)(3)', text[offsets[0]:offsets[1]])

    def test_sub_comment(self):
        text = "refer to comment 36(a)(2)-3 of thing"
        result = self.parser.process(Node(text, label=['222', '87']))
        self.assertEqual(1, len(result))
        self.assertEqual(['222', '36', 'a', '2', Node.INTERP_MARK, '3'],
                         result[0]['citation'])
        offsets = result[0]['offsets'][0]
        self.assertEqual('36(a)(2)-3', text[offsets[0]:offsets[1]])

    def test_sub_comment2(self):
        text = "See comment 3(b)(1)-1.v."
        result = self.parser.process(Node(text, label=['222', '87']))
        self.assertEqual(1, len(result))
        self.assertEqual(['222', '3', 'b', '1', Node.INTERP_MARK, '1', 'v'],
                         result[0]['citation'])
        offsets = result[0]['offsets'][0]
        #   Note the final period is not included
        self.assertEqual('3(b)(1)-1.v', text[offsets[0]:offsets[1]])

    def test_multiple_comments(self):
        text = "See, e.g., comments 31(b)(1)(iv)-1 and 31(b)(1)(vi)-1"
        result = self.parser.process(Node(text, label=['222', '87']))
        self.assertEqual(2, len(result))
        self.assertEqual(['222', '31', 'b', '1', 'iv', Node.INTERP_MARK, '1'],
                         result[0]['citation'])
        offsets = result[0]['offsets'][0]
        self.assertEqual('31(b)(1)(iv)-1', text[offsets[0]:offsets[1]])
        self.assertEqual(['222', '31', 'b', '1', 'vi', Node.INTERP_MARK, '1'],
                         result[1]['citation'])
        offsets = result[1]['offsets'][0]
        self.assertEqual('31(b)(1)(vi)-1', text[offsets[0]:offsets[1]])

    def test_paren_in_interps(self):
        text = "covers everything except paragraph (d)(3)(i) of this section"
        result = self.parser.process(
            Node(text, label=['222', '87', Node.INTERP_MARK]))
        self.assertEqual(1, len(result))
        self.assertEqual(['222', '87', 'd', '3', 'i'], result[0]['citation'])
        offsets = result[0]['offsets'][0]
        self.assertEqual('(d)(3)(i)', text[offsets[0]:offsets[1]])

        result = self.parser.process(
            Node(text, label=['222', '87', 'd', '3', Node.INTERP_MARK]))
        self.assertEqual(1, len(result))
        self.assertEqual(['222', '87', 'd', '3', 'i'], result[0]['citation'])
        offsets = result[0]['offsets'][0]
        self.assertEqual('(d)(3)(i)', text[offsets[0]:offsets[1]])

    def test_cfr_format(self):
        """We aren't processing this form yet"""
        text = "12 CFR 1026.3(d)"
        result = self.parser.process(Node(text, label=['1111']))
        self.assertEqual(None, result)

    def test_pre_process(self):
        tree = Node(label=['1111', '2', '3'],
                    children=[Node(label=['222', '1', '1']),
                              Node(label=['222', '1', '1'],
                                   children=[Node(label=['111', '34'])])])
        parser = internal_citations.InternalCitationParser(tree)
        parser.pre_process()
        self.assertEqual(parser.known_citations, set([
            ('1111', '2', '3'), ('222', '1', '1'), ('111', '34')]))

    def test_verify_citations(self):
        tree = Node(label=['1111', '2', '3'],
                    children=[Node(label=['222', '1', '1']),
                              Node(label=['222', '1', '1'],
                                   children=[Node(label=['111', '34'])])])
        parser = internal_citations.InternalCitationParser(tree)
        parser.pre_process()
        parser.verify_citations = False
        text = 'Section 111.34 and paragraph (c)'
        result = parser.process(Node(text))
        self.assertEqual(2, len(result))

        parser.verify_citations = True
        result = parser.process(Node(text))
        self.assertEqual(1, len(result))
        start, end = result[0]['offsets'][0]
        self.assertEqual('111.34', text[start:end].strip())

    def test_internal_cfr_format(self):
        text = 'under 11 CFR 110.14 are not subject'
        self.parser.cfr_title = '11'
        result = self.parser.process(Node(text, label=['110', '1']))
        self.assertEqual(1, len(result))
        self.assertEqual(['110', '14'], result[0]['citation'])
        offsets = result[0]['offsets'][0]
        self.assertEqual('11 CFR 110.14', text[offsets[0]:offsets[1]])
        # Verify that CFR citations from other titles do not get caught.
        self.parser.cfr_title = '12'
        result = self.parser.process(Node(text, label=['110', '1']))
        self.assertEqual(None, result)
        # Verify that CFR citations from other parts do not get caught.
        self.parser.cfr_title = '11'
        result = self.parser.process(Node(text, label=['111', '1']))
        self.assertEqual(None, result)

    def test_multiple_internal_cfr(self):
        text = 'prohibited from making contributions under 11 CFR 110.19, '
        text += '110.20, and 110.21'
        self.parser.cfr_title = '11'
        result = self.parser.process(Node(text, label=['110', '1']))
        self.assertEqual(3, len(result))
        self.assertEqual(['110', '19'], result[0]['citation'])
        offsets = result[0]['offsets'][0]
        self.assertEqual('11 CFR 110.19', text[offsets[0]:offsets[1]])
        self.assertEqual(['110', '20'], result[1]['citation'])
        offsets = result[1]['offsets'][0]
        self.assertEqual('110.20', text[offsets[0]:offsets[1]])
        self.assertEqual(['110', '21'], result[2]['citation'])
        offsets = result[2]['offsets'][0]
        self.assertEqual('110.21', text[offsets[0]:offsets[1]])

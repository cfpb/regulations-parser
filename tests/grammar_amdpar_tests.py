#vim: set encoding=utf-8
from unittest import TestCase

from regparser.grammar import tokens
from regparser.grammar.amdpar import *


def parse_text(text):
    return [m[0] for m, _, _ in token_patterns.scanString(text)]


class GrammarAmdParTests(TestCase):

    def test_tokenlist_iteratable(self):
        token_list = tokens.TokenList([
            tokens.Paragraph([1005, None, 1]),
            tokens.Paragraph([1005, None, 2]),
            tokens.Paragraph([1005, None, 3]),
        ])

        count = 1
        for t in token_list:
            self.assertEqual(t.label, [1005, None, count])
            count += 1
        self.assertEqual(count, 4)

    def test_example1(self):
        text = u"In § 9876.1, revise paragraph (b) to read as follows"
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.Context(['9876', None, '1'], certain=True),
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Paragraph([None, None, None, 'b'])
        ])

    def test_example2(self):
        text = u"In § 7654.2, revise the introductory text to read as"
        text += " follows"
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.Context(['7654', None, '2'], certain=True),
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Paragraph([], field=tokens.Paragraph.TEXT_FIELD)
        ])

    def test_example3(self):
        text = "6. Add subpart B to read as follows:"
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.Verb(tokens.Verb.POST, active=True),
            tokens.Context([None, 'Subpart:B'], certain=False)
        ])

    def test_example4(self):
        text = "b. Add Model Forms E-11 through E-15."
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.Verb(tokens.Verb.POST, active=True),
            tokens.TokenList([
                tokens.Paragraph([None, 'Appendix:E', '11']),
                tokens.Paragraph([None, 'Appendix:E', '12']),
                tokens.Paragraph([None, 'Appendix:E', '13']),
                tokens.Paragraph([None, 'Appendix:E', '14']),
                tokens.Paragraph([None, 'Appendix:E', '15'])
            ])
        ])

    def test_example5(self):
        text = "7. In Supplement I to part 6363:"
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.Context(['6363', 'Interpretations'], certain=True)
        ])

    def test_example6(self):
        """Although this includes the term 'Commentary', we assume these are
        not interpretations and handle the problem of merging later"""
        text = u"a. Add new Commentary for §§ 6363.30, 6363.31, 6363.32,"
        text += " 6363.33, 6363.34, 6363.35, and 6363.36."
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.Verb(tokens.Verb.POST, active=True),
            tokens.TokenList([
                tokens.Paragraph(['6363', None, '30']),
                tokens.Paragraph(['6363', None, '31']),
                tokens.Paragraph(['6363', None, '32']),
                tokens.Paragraph(['6363', None, '33']),
                tokens.Paragraph(['6363', None, '34']),
                tokens.Paragraph(['6363', None, '35']),
                tokens.Paragraph(['6363', None, '36']),
            ])
        ])

    def test_example7(self):
        text = u'1. On page 1234, in the second column, in Subpart A, § '
        text += '4444.3(a) is corrected to read as follows:'
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.Context([None, 'Subpart:A'], certain=True),
            tokens.Paragraph(['4444', None, '3', 'a']),
            tokens.Verb(tokens.Verb.PUT, active=False),
        ])

    def test_example8(self):
        text = "2. On page 8765 through 8767, in Appendix A to Part 1234,"
        text += "Model Forms A-15 through A-19 are corrected to read as "
        text += "follows:"
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.Context(['1234', 'Appendix:A'], certain=True),
            tokens.TokenList([
                tokens.Paragraph([None, 'Appendix:A', '15']),
                tokens.Paragraph([None, 'Appendix:A', '16']),
                tokens.Paragraph([None, 'Appendix:A', '17']),
                tokens.Paragraph([None, 'Appendix:A', '18']),
                tokens.Paragraph([None, 'Appendix:A', '19'])
            ]),
            tokens.Verb(tokens.Verb.PUT, active=False),
        ])

    def text_example9(self):
        text = u"3. Amend § 5397.31 to revise paragraphs (a)(3)(ii), "
        text += "(a)(3)(iii), and (b)(3); and add paragraphs (a)(3)(iv), "
        text += "(a)(5)(iv), and (b)(2)(vii) to read as follows:"
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.Context(['5397', None, '31']),
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.TokenList([
                tokens.Paragraph([None, None, None, 'a', '3', 'ii']),
                tokens.Paragraph([None, None, None, 'a', '3', 'iii']),
                tokens.Paragraph([None, None, None, 'b', '3'])
            ]),
            tokens.Verb(tokens.Verb.POST, active=True),
            tokens.TokenList([
                tokens.Paragraph([None, None, None, 'a', '3', 'iv']),
                tokens.Paragraph([None, None, None, 'a', '5', 'iv']),
                tokens.Paragraph([None, None, None, 'b', '2', 'vii'])
            ]),
        ])

    def test_example10(self):
        text = "paragraph (b) and the introductory text of paragraph (c)"
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.Paragraph([None, None, None, 'b']),
            tokens.AndToken(),
            tokens.Paragraph([None, None, None, 'c'],
                             field=tokens.Paragraph.TEXT_FIELD)
        ])

    def test_example11(self):
        text = u"Amend § 1005.36 to revise the section heading and "
        text += "paragraphs (a) and (b), and to add paragraph (d) to read "
        text += "as follows:"
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.Context(['1005', None, '36']),
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Paragraph([], field=tokens.Paragraph.HEADING_FIELD),
            tokens.AndToken(),
            tokens.TokenList([
                tokens.Paragraph([None, None, None, 'a']),
                tokens.Paragraph([None, None, None, 'b']),
            ]),
            tokens.AndToken(),
            tokens.Verb(tokens.Verb.POST, active=True),
            tokens.Paragraph([None, None, None, 'd']),
        ])

    def test_example12(self):
        text = "comment 31(b), amend paragraph 31(b)(2) by adding "
        text += "paragraphs 4 through 6;"
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.Context([None, 'Interpretations', '31', '(b)']),
            tokens.Context([None, 'Interpretations', '31', '(b)(2)']),
            tokens.Verb(tokens.Verb.POST, active=True),
            tokens.TokenList([
                tokens.Paragraph([None, 'Interpretations', None, None, '4']),
                tokens.Paragraph([None, 'Interpretations', None, None, '5']),
                tokens.Paragraph([None, 'Interpretations', None, None, '6'])
            ])
        ])

    def test_example13(self):
        text = "h. Under Section 6363.36, add comments 36(a), 36(b) and "
        text += "36(d)."
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.Context(['6363', None, '36'], certain=True),
            tokens.Verb(tokens.Verb.POST, active=True),
            #   We assume that lists of comments are not context
            tokens.TokenList([
                tokens.Paragraph([None, 'Interpretations', '36', '(a)']),
                tokens.Paragraph([None, 'Interpretations', '36', '(b)']),
                tokens.Paragraph([None, 'Interpretations', '36', '(d)']),
            ])
        ])

    def test_example14(self):
        text = "and removing paragraph (c)(5) to read as follows:"
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.AndToken(),
            tokens.Verb(tokens.Verb.DELETE, active=True),
            tokens.Paragraph([None, None, None, 'c', '5'])
        ])

    def test_example15(self):
        text = "paragraphs (a)(1)(iii), (a)(1)(iv)(B), (c)(2) introductory "
        text += 'text and (c)(2)(ii)(A)(<E T="03">2</E>) redesignating '
        text += "paragraph (c)(2)(iii) as paragraph (c)(2)(iv),"
        result = parse_text(text)
        expected = [tokens.TokenList([
            tokens.Paragraph([None, None, None, 'a', '1', 'iii']),
            tokens.Paragraph([None, None, None, 'a', '1', 'iv', 'B']),
            tokens.Paragraph(
                [None, None, None, 'c', '2'],
                field=tokens.Paragraph.TEXT_FIELD),
            tokens.Paragraph([None, None, None, 'c', '2', 'ii', 'A'])]),
            tokens.Verb(tokens.Verb.MOVE, active=True),
            tokens.Paragraph([None, None, None, 'c', '2', 'iii']),
            tokens.Paragraph([None, None, None, 'c', '2', 'iv'])]
        self.assertEqual(result, expected)

    def test_example16(self):
        text = " A-30(a), A-30(b), A-30(c), A-30(d) are added"
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.TokenList([
                tokens.Paragraph([None, "Appendix:A", "30", "a"]),
                tokens.Paragraph([None, "Appendix:A", "30", "b"]),
                tokens.Paragraph([None, "Appendix:A", "30", "c"]),
                tokens.Paragraph([None, "Appendix:A", "30", "d"]),
            ]),
            tokens.Verb(tokens.Verb.POST, active=False),
        ])

    def test_example17(self):
        text = "viii. Under comment 31(c)(4), paragraph 2.xi.is added."
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.Context([None, 'Interpretations', '31', '(c)(4)'],
                           certain=True),
            tokens.Paragraph([None, 'Interpretations', None, None, '2', 'xi']),
            tokens.Verb(tokens.Verb.POST, active=False)
        ])

    def test_example18(self):
        text = 'Section 106.52(b)(1)(ii)(A) and (B) is revised'
        text += ' to read as follows'
        result = parse_text(text)

        self.assertEqual(result, [
            tokens.TokenList([
                tokens.Paragraph(['106', None, '52', 'b', '1', 'ii', 'A']),
                tokens.Paragraph([None, None, None, None, None, None, 'B']),
            ]),
            tokens.Verb(tokens.Verb.PUT, active=False)
        ])

    def test_example_19(self):
        text = u"Section 106.43 is amended by revising paragraphs"
        text += " (a)(3)(ii) and (iii), (b)(4), (e)(1) and (g)(1)(ii)(B),"
        text += " and adding new paragraphs (a)(3)(iv) through (vi), (e)(5)"
        text += " and (e)(6) to read as follows:"

        result = parse_text(text)
        result = [l for l in result if isinstance(l, tokens.TokenList)]
        token_list = result[0]

        iii = tokens.Paragraph([None, None, None, None, None, 'iii'])
        self.assertTrue(iii in token_list)

        second_token_list = result[1]

        v = tokens.Paragraph([None, None, None, 'a', '3', 'v'])
        self.assertTrue(v in second_token_list)

    def test_example_20(self):
        text = "Section 105.32 is amended by"
        text += " adding paragraph (b)(3) through (6)"

        result = parse_text(text)
        result = [l for l in result if isinstance(l, tokens.TokenList)]
        token_list = result[0]

        b3 = tokens.Paragraph([None, None, None, 'b', '3'])
        self.assertTrue(b3 in token_list)

        b4 = tokens.Paragraph([None, None, None, 'b', '4'])
        self.assertTrue(b4 in token_list)

        b5 = tokens.Paragraph([None, None, None, 'b', '5'])
        self.assertTrue(b5 in token_list)

        b6 = tokens.Paragraph([None, None, None, None, '6'])
        self.assertTrue(b6 in token_list)

    def test_reserving(self):
        text = "Section 105.32 is amended by"
        text += " removing and reserving paragraph (b)(2)"

        result = [m[0] for m, _, _ in token_patterns.scanString(text)]
        reserve_token = tokens.Verb(tokens.Verb.RESERVE, active=True)
        self.assertTrue(reserve_token in result)

    def test_example_21(self):
        text = "Section 102.36 is amended by"
        text += " revising the heading of paragraph (a)"

        result = parse_text(text)
        paragraph = [p for p in result if isinstance(p, tokens.Paragraph)][0]
        p_object = tokens.Paragraph([None, None, None, 'a'], field='heading')
        self.assertEqual(p_object, paragraph)

    def test_example_22(self):
        text = "comment 33(c)-5 is redesignated as comment 33(c)-6 and "
        text += "republished, and comment 33(c)-(5) is added."

        result = parse_text(text)
        self.assertEqual(7, len(result))
        old, verb, new, and1, and2, new_new, verb2 = result
        self.assertEqual(old.label,
                         [None, 'Interpretations', '33', '(c)', '5'])
        self.assertEqual(new.label,
                         [None, 'Interpretations', '33', '(c)', '6'])
        self.assertEqual(new_new.label,
                         [None, 'Interpretations', '33', '(c)', '5'])

    def test_example_23(self):
        text = "comment 33(c)-5 is redesignated comment 33(c)-6 and revised"

        result = parse_text(text)
        self.assertEqual(4, len(result))
        old, redes, new, revised = result
        self.assertEqual(revised, tokens.Verb(tokens.Verb.PUT, active=False,
                                              and_prefix=True))

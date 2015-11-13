# vim: set encoding=utf-8
from unittest import TestCase

from regparser.grammar import amdpar, tokens


def parse_text(text):
    return [m[0] for m, _, _ in amdpar.token_patterns.scanString(text)]


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
                tokens.Paragraph([None, "Appendix:A", "30(a)"]),
                tokens.Paragraph([None, "Appendix:A", "30(b)"]),
                tokens.Paragraph([None, "Appendix:A", "30(c)"]),
                tokens.Paragraph([None, "Appendix:A", "30(d)"]),
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

        result = parse_text(text)
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
        text = "%(mark)s 33(c)-5 is redesignated as %(mark)s 33(c)-6 and "
        text += "republished, and %(mark)s 33(c)-(5) is added."
        texts = [text % {"mark": marker}
                 for marker in ("comment", "paragraph")]

        for text in texts:
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

    def test_example_24(self):
        text = "a. Revising the paragraph (c) subject heading and "
        text += "paragraphs (c)(1)(ii) through (iv);"
        result = parse_text(text)
        self.assertEqual(4, len(result))
        verb, subj, and_tok, toklist = result
        self.assertTrue(verb.match(tokens.Verb))
        self.assertTrue(subj.match(tokens.Paragraph,
                                   field=tokens.Paragraph.TEXT_FIELD))
        self.assertTrue(and_tok.match(tokens.AndToken))
        self.assertTrue(toklist.match(tokens.TokenList))

    def test_example_25(self):
        texts = ["Revising the heading of 12(c)",
                 "Revising the heading for 12(c)",
                 "Revising heading 12(c)"]
        for text in texts:
            result = parse_text(text)
            self.assertEqual(2, len(result))
            verb, par = result
            self.assertTrue(verb.match(tokens.Verb))
            self.assertTrue(par.match(
                tokens.Paragraph,
                label=[None, 'Interpretations', '12', '(c)'],
                field=tokens.Paragraph.HEADING_FIELD))

    def test_example_26(self):
        text = "Entries for 15(a), (b)(3) and (4) are added."
        result = parse_text(text)
        self.assertEqual(2, len(result))
        toklist, verb = result
        self.assertTrue(toklist.match(tokens.TokenList))
        self.assertTrue(verb.match(tokens.Verb))

        self.assertEqual(3, len(toklist.tokens))
        a, b3, b4 = toklist.tokens
        self.assertTrue(a.match(
            tokens.Paragraph, label=[None, None, '15', 'a']))
        self.assertTrue(b3.match(
            tokens.Paragraph, label=[None, None, None, 'b', '3']))
        self.assertTrue(b4.match(
            tokens.Paragraph, label=[None, None, None, None, '4']))

    def test_example_27(self):
        text = "The heading for Section 1234.56-Toastfully Eggselent is "
        text += "revised"
        result = parse_text(text)
        self.assertEqual(2, len(result))
        par, verb = result
        self.assertTrue(verb.match(tokens.Verb, verb=tokens.Verb.PUT))
        self.assertTrue(par.match(tokens.Paragraph,
                                  label=['1234', None, '56'],
                                  field=tokens.Paragraph.HEADING_FIELD))

    def test_example_28(self):
        text = "Section 1111.22 is amended by adding introductory text to "
        text += "paragraph (a) and revising paragraphs (b), (f) "
        text += "introductory text, (g) introductory text, and (h) "
        text += "introductory text to read as follows:"
        result = parse_text(text)
        self.assertEqual(6, len(result))
        context, add, a, andToken, revise, lst = result
        self.assertTrue(context.match(tokens.Context,
                                      label=['1111', None, '22']))
        self.assertTrue(add.match(tokens.Verb, verb=tokens.Verb.POST))
        self.assertTrue(a.match(tokens.Paragraph,
                                label=[None, None, None, 'a'],
                                field=tokens.Paragraph.TEXT_FIELD))
        self.assertTrue(andToken.match(tokens.AndToken))
        self.assertTrue(lst.match(tokens.TokenList))

    def test_example_29(self):
        text = "The subheading Appendix R-Reeeeeeally? is revised."
        result = parse_text(text)
        self.assertEqual(2, len(result))
        subheading, revised = result
        self.assertTrue(subheading.match(
            tokens.Paragraph, label=[None, 'Interpretations', 'R', '()'],
            field=tokens.Paragraph.HEADING_FIELD))
        self.assertTrue(revised.match(tokens.Verb, verb=tokens.Verb.PUT))

    def test_example_30(self):
        for text in ("The heading for Paragraph 29(r)(6) is revised.",
                     "The heading of comment 29(r)(6) is revised."):
            result = parse_text(text)
            self.assertEqual(2, len(result))
            heading, revised = result
            self.assertTrue(heading.match(
                tokens.Paragraph, label=[None, 'Interpretations', '29',
                                         '(r)(6)'],
                field=tokens.Paragraph.HEADING_FIELD))
            self.assertTrue(revised.match(tokens.Verb, verb=tokens.Verb.PUT))

    def test_example_31(self):
        text = "Introductory text to paragraph 1 is revised."
        result = parse_text(text)
        self.assertEqual(2, len(result))
        paragraph, verb = result
        self.assertTrue(paragraph.match(
            tokens.Paragraph, label=[None, 'Interpretations', None, None, '1'],
            field=tokens.Paragraph.TEXT_FIELD))
        self.assertTrue(verb.match(tokens.Verb, verb=tokens.Verb.PUT))

    def test_example_32(self):
        text = "Title A-30 is removed"
        result = parse_text(text)
        self.assertEqual(2, len(result))
        paragraph, verb = result
        self.assertTrue(paragraph.match(
            tokens.Paragraph, label=[None, 'Appendix:A', '30']))
        self.assertTrue(verb.match(tokens.Verb, verb=tokens.Verb.DELETE))

    def test_example_33(self):
        text = "Referencing A-30(a)(5) through A-30(a)(8)"
        result = parse_text(text)
        self.assertEqual(1, len(result))
        self.assertTrue(result[0].match(tokens.TokenList))
        self.assertEqual(4, len(result[0].tokens))
        a5, a6, a7, a8 = result[0].tokens
        self.assertTrue(a5.match(
            tokens.Paragraph, label=[None, 'Appendix:A', '30(a)(5)']))
        self.assertTrue(a6.match(
            tokens.Paragraph, label=[None, 'Appendix:A', '30(a)(6)']))
        self.assertTrue(a7.match(
            tokens.Paragraph, label=[None, 'Appendix:A', '30(a)(7)']))
        self.assertTrue(a8.match(
            tokens.Paragraph, label=[None, 'Appendix:A', '30(a)(8)']))

    def test_example_34(self):
        text = "Appendix H to Part 1234 is amended by revising the heading "
        text += "of H-30(C) to read as follows:"
        result = parse_text(text)
        self.assertEqual(3, len(result))
        context, verb, heading = result
        self.assertTrue(context.match(
            tokens.Context, label=['1234', 'Appendix:H']))
        self.assertTrue(verb.match(tokens.Verb, verb=tokens.Verb.PUT))
        self.assertTrue(heading.match(
            tokens.Paragraph, label=[None, 'Appendix:H', '30(C)'],
            field=tokens.Paragraph.HEADING_FIELD))

    def test_example_35(self):
        text = "5. Section 100.94 is added to subpart C to read as follows:"
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.Context(['100', None, '94'], certain=False),
            tokens.Verb(tokens.Verb.POST, active=False, and_prefix=False),
            tokens.Context([None, 'Subpart:C'], certain=True)
        ])

    def test_example36(self):
        text = (u'In Appendix A to Part 1002 revise [label:1002-A-p1-2-d] to '
                u'read:')
        result = parse_text(text)
        self.assertEqual(result, [
            tokens.Context(['1002', 'Appendix:A'], certain=True),
            tokens.Verb(tokens.Verb.PUT, active=True, and_prefix=False),
            tokens.Paragraph(['1002', 'Appendix:A', 'p1', '2', 'd'],
                             field=None)
        ])

    def test_paragraph_of(self):
        text = u"12. Paragraph (c)(1)(iv) of § 4.9 is revised"
        result = parse_text(text)
        self.assertEqual(2, len(result))
        paragraph, verb = result

        self.assertTrue(paragraph.match(
            tokens.Paragraph, label=['4', None, '9', 'c', '1', 'iv']))
        self.assertTrue(verb.match(
            tokens.Verb, verb=tokens.Verb.PUT))

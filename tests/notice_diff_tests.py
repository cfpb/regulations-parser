#vim: set encoding=utf-8
from unittest import TestCase

from lxml import etree

from regparser.grammar import tokens
from regparser.notice.diff import *

class NoticeDiffTests(TestCase):

    def test_clear_between(self):
        xml = u"""
        <ROOT>Some content[ removed]
            <CHILD>Split[ it
                <SUB>across children</SUB>
                ]
            </CHILD>
        </ROOT>
        """.strip()
        result = clear_between(etree.fromstring(xml), '[', ']')
        cleaned = u"""
        <ROOT>Some content
            <CHILD>Split
            </CHILD>
        </ROOT>
        """.strip()
        self.assertEqual(cleaned, etree.tostring(result))

    def test_remove_char(self):
        xml = u"""<ROOT> Some stuff▸, then a bit more◂.</ROOT>"""
        result = remove_char(remove_char(etree.fromstring(xml), u'▸'), u'◂')
        cleaned = u"""<ROOT> Some stuff, then a bit more.</ROOT>"""
        self.assertEqual(cleaned, etree.tostring(result))

    def test_make_amendments(self):
        tokenized = [
            tokens.Paragraph(['111']),
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Paragraph(['222']),
            tokens.Paragraph(['333']),
            tokens.Paragraph(['444']),
            tokens.Verb(tokens.Verb.DELETE, active=True),
            tokens.Paragraph(['555']),
            tokens.Verb(tokens.Verb.MOVE, active=True),
            tokens.Paragraph(['666']),
            tokens.Paragraph(['777'])
        ]
        amends = make_amendments(tokenized)
        self.assertEqual(amends, [ 
            (tokens.Verb.PUT, '222'), (tokens.Verb.PUT, '333'), 
            (tokens.Verb.PUT, '444'), (tokens.Verb.DELETE, '555'), 
            (tokens.Verb.MOVE, ('666', '777'))
        ])

    def test_compress_context_simple(self):
        tokenized = [
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Context(['9876', 'Subpart:A']),  #   part 9876, subpart A
            tokens.Context([None, None, '12']), #   section 12
            tokens.Paragraph([None, None, None, 'f', '4']),  # 12(f)(4)
            tokens.Context([None, None, None, 'g']), # 12(f)
            tokens.Paragraph([None, None, None, None, '1']),    #   12(g)(1)
        ]
        converted, final_ctx = compress_context(tokenized, [])
        self.assertEqual(converted, [
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Paragraph(['9876', 'Subpart:A', '12', 'f', '4']),
            tokens.Paragraph(['9876', 'Subpart:A', '12', 'g', '1'])
        ])
        self.assertEqual(['9876', 'Subpart:A', '12', 'g', '1'], final_ctx)

    def test_compress_context_initial_context(self):
        tokenized = [tokens.Paragraph([None, None, None, 'q'])]
        converted, _ = compress_context(tokenized, ['111', None, '12'])
        self.assertEqual(converted, 
            [tokens.Paragraph(['111', None, '12', 'q'])])

    def test_compress_context_interpretations(self):
        tokenized = [
            tokens.Context(['123', 'Interpretations']),
            tokens.Paragraph([None, None, '12', 'a', '2', 'iii']),
            tokens.Paragraph([None, 'Interpretations', None, None, '3', 'v']),
            tokens.Context([None, 'Appendix:R']),
            tokens.Paragraph([None, 'Interpretations', None, None, '5'])
        ]
        converted, _ = compress_context(tokenized, [])
        self.assertEqual(converted, [
            tokens.Paragraph(['123', 'Interpretations', '12', '(a)(2)(iii)',
                '3', 'v']),
            #   None because we are missing a layer
            tokens.Paragraph(['123', 'Interpretations', 'Appendix:R', None,
                '5'])
        ])

    def test_compress(self):
        self.assertEqual([1,2,3], compress([1,2,3], []))
        self.assertEqual([1,6,3], compress([1,2,3,4,5], [None,6,None]))
        self.assertEqual([2,2,5,6], compress([1,2], [2,None,5,6]))

    def test_separate_tokenlist(self):
        tokenized = [
            tokens.Context(['1']),
            tokens.TokenList([
                tokens.Verb(tokens.Verb.MOVE, active=True),
                tokens.Context([None, '2'])
            ]),
            tokens.Paragraph([None, '3']),
            tokens.TokenList([tokens.Paragraph([None, None, 'b'])])
        ]
        converted = separate_tokenlist(tokenized)
        self.assertEqual(converted, [
            tokens.Context(['1']),
            tokens.Verb(tokens.Verb.MOVE, active=True),
            tokens.Context([None, '2']),
            tokens.Paragraph([None, '3']),
            tokens.Paragraph([None, None, 'b'])
        ])

    def test_context_to_paragraph(self):
        tokenized = [
            tokens.Context(['1']),
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Context(['2']),
            tokens.Context(['3'], certain=True),
            tokens.Context(['4'])
        ]
        converted = context_to_paragraph(tokenized)
        self.assertEqual(converted, [
            tokens.Context(['1']),
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Paragraph(['2']),
            tokens.Context(['3'], certain=True),
            tokens.Paragraph(['4'])
        ])

    def test_context_to_paragraph_exceptions(self):
        tokenized = [
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Context(['2']),
            tokens.Paragraph(['3'])
        ]
        converted = context_to_paragraph(tokenized)
        self.assertEqual(tokenized, converted)

        tokenized = [
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Context(['2']),
            tokens.TokenList([tokens.Paragraph(['3'])])
        ]
        converted = context_to_paragraph(tokenized)
        self.assertEqual(tokenized, converted)

    def test_switch_passive(self):
        tokenized = [
            tokens.Context(['1']),
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Context(['2'])
        ]
        converted = switch_passive(tokenized)
        self.assertEqual(tokenized, converted)

        tokenized = [
            tokens.Context(['1']),
            tokens.Verb(tokens.Verb.PUT, active=False),
            tokens.Context(['2']),
            tokens.Context(['3']),
            tokens.Verb(tokens.Verb.MOVE, active=False),
        ]
        converted = switch_passive(tokenized)
        self.assertEqual(converted, [
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Context(['1']),
            tokens.Verb(tokens.Verb.MOVE, active=True),
            tokens.Context(['2']),
            tokens.Context(['3']),
        ])

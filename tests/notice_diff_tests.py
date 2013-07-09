#vim: set encoding=utf-8
from unittest import TestCase

from lxml import etree

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

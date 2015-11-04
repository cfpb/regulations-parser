from unittest import TestCase

from lxml import etree

from regparser.notice import util


class NoticeUtilTests(TestCase):
    def test_prepost_pend_spaces(self):
        for txt in ("a<em>bad</em>sentence", "a <em>bad</em>sentence",
                    "a<em>bad</em> sentence", "a <em>bad</em> sentence"):
            xml = etree.fromstring("<ROOT>This is " + txt + "</ROOT>")
            util.prepost_pend_spaces(xml.xpath("//em")[0])
            self.assertEqual(etree.tostring(xml),
                             '<ROOT>This is a <em>bad</em> sentence</ROOT>')

        xml = etree.fromstring(
            "<ROOT>"
            + "@<em>smith</em>: what<em>do</em>you think about $<em>15</em>"
            + "? That's <em>9</em>%!</ROOT>")
        for em in xml.xpath("//em"):
            util.prepost_pend_spaces(em)
        self.assertEqual(etree.tostring(xml),
                         '<ROOT>@<em>smith</em>: what <em>do</em> you think'
                         + " about $<em>15</em>? That's <em>9</em>%!</ROOT>")

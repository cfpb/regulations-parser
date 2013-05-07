from lxml import etree
from parser.rule.parse import *
from unittest import TestCase

class RuleParseTest(TestCase):

    def test_find_section_by_section(self):
        sxs_xml = """
            <HD SOURCE="HD2">Sub Section</HD>
            <P>Content</P>
            <HD SOURCE="HD3">Sub sub section</HD>
            <P>Sub Sub Content</P>"""
        full_xml = """
        <ROOT>
            <SUPLINF>
                <HD SOURCE="HED">Supplementary Info</HD>
                <HD SOURCE="HD1">Stuff Here</HD>
                <P>Some Content</P>
                <HD SOURCE="HD1">X. Section-by-Section Analysis</HD>
                %s
                <HD SOURCE="HD1">Section that follows</HD>
                <P>Following Content</P>
            </SUPLINF>
        </ROOT>""" % sxs_xml

        sxs = etree.fromstring("<ROOT>" + sxs_xml + "</ROOT>")
        #   Must use text field since the nodes are not directly comparable
        sxs_texts = map(lambda el: el.text, list(sxs.xpath("/ROOT/*")))

        computed = find_section_by_section(etree.fromstring(full_xml))
        self.assertEqual(sxs_texts, map(lambda el: el.text, computed))

    def test_fetch_document_number(self):
        xml = """
        <ROOT>
            <CHILD />
            <CHILD>Body</CHILD>
            <CHILD>
                <FRDOC>[FR Doc. 2001-10 Filed 1-20-01; 12:52 am]</FRDOC>
            </CHILD>
            <CHILD>Body</CHILD>
        </ROOT>
        """
        self.assertEqual("200110",
                fetch_document_number(etree.fromstring(xml)))

    def test_parse_into_label(self):
        self.assertEqual("101.22", 
                parse_into_label("Section 101.22Stuff", "101"))
        self.assertEqual("101.22(d)", 
                parse_into_label("22(d) Content", "101"))
        self.assertEqual("101.22(d)(5)", 
                parse_into_label("22(d)(5) Content", "101"))
        self.assertEqual("101.22(d)(5)(x)", 
                parse_into_label("22(d)(5)(x) Content", "101"))
        self.assertEqual("101.22(d)(5)(x)(Q)", 
                parse_into_label("22(d)(5)(x)(Q) Content", "101"))

        self.assertEqual(None,
                parse_into_label("Application of this rule", "101"))


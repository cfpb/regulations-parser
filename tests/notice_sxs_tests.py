#vim: set encoding=utf-8
from lxml import etree
from regparser.notice.sxs import *
from unittest import TestCase


class NoticeSxsTests(TestCase):
    def test_find_page(self):
        xml = """<ROOT>
            <P />
            Text
            <P />
            <PRTPAGE P="333" />
            <P />
            <PRTPAGE />
            <P />
            <PRTPAGE P="334" />
        </ROOT>"""
        xml = etree.fromstring(xml)
        for l in range(0, 6):
            self.assertEqual(332, find_page(xml, l, 332))
        for l in range(6, 10):
            self.assertEqual(333, find_page(xml, l, 332))
        for l in range(10, 15):
            self.assertEqual(334, find_page(xml, l, 332))

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

    def test_find_section_by_section_not_present(self):
        full_xml = """
        <ROOT>
            <SUPLINF>
                <HD SOURCE="HED">Supplementary Info</HD>
                <HD SOURCE="HD1">This is not sxs Analysis</HD>
                <P>Stuff</P>
                <P>Stuff2</P>
                <FTNT>Foot Note</FTNT>
            </SUPLINF>
        </ROOT>"""
        self.assertEqual([], find_section_by_section(etree.fromstring(
            full_xml)))

    def test_build_section_by_section(self):
        xml = """
        <ROOT>
            <HD SOURCE="HD3">Section Header</HD>
            <P>Content 1</P>
            <P>Content 2</P>
            <HD SOURCE="HD4">Sub Section Header</HD>
            <P>Content 3</P>
            <HD SOURCE="HD4">Another</HD>
            <P>Content 4</P>
            <HD SOURCE="HD3">4(b) Header</HD>
            <P>Content 5</P>
        </ROOT>"""
        sxs = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = build_section_by_section(sxs, '100', 83)
        self.assertEqual(2, len(structures))
        self.assertEqual(structures[0], {
            'title': 'Section Header',
            'paragraphs': [
                'Content 1',
                'Content 2'
                ],
            'children': [
                {
                    'title': 'Sub Section Header',
                    'paragraphs': ['Content 3'],
                    'children': [],
                    'page': 83
                },
                {
                    'title': 'Another',
                    'paragraphs': ['Content 4'],
                    'children': [],
                    'page': 83
                }],
            'page': 83
            })
        self.assertEqual(structures[1], {
            'title': '4(b) Header',
            'paragraphs': ['Content 5'],
            'label': '100-4-b',
            'page': 83,
            'children': []
            })

    def test_build_section_by_section_footnotes(self):
        """We only account for paragraph tags right now"""
        xml = """
        <ROOT>
            <HD SOURCE="HD3">Section Header</HD>
            <P>Content 1</P>
            <FTNT>Content A</FTNT>
            <P>Content 2</P>
        </ROOT>"""
        sxs = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = build_section_by_section(sxs, '100', 21)
        self.assertEqual(1, len(structures))
        self.assertEqual(structures[0], {
            'title': 'Section Header',
            'paragraphs': [
                'Content 1',
                'Content 2',
                ],
            'children': [],
            'page': 21
            })

    def test_build_section_by_section_label(self):
        """Check that labels are being added correctly"""
        xml = """
        <ROOT>
            <HD SOURCE="HD2">Section 99.3 Info</HD>
            <P>Content 1</P>
            <HD SOURCE="HD3">3(q)(4) More Info</HD>
            <P>Content 2</P>
        </ROOT>"""
        sxs = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = build_section_by_section(sxs, '99', 2323)
        self.assertEqual(1, len(structures))
        self.assertEqual(structures[0], {
            'title': 'Section 99.3 Info',
            'label': '99-3',
            'paragraphs': ['Content 1'],
            'page': 2323,
            'children': [{
                'title': '3(q)(4) More Info',
                'label': '99-3-q-4',
                'paragraphs': ['Content 2'],
                'page': 2323,
                'children': []
            }]
        })

    def test_build_section_by_section_extra_tags(self):
        """Check that labels are being added correctly"""
        xml = """
        <ROOT>
            <HD SOURCE="HD2">Section 99.3 Info</HD>
            <P>Content<PRTPAGE P="50249"/>1</P>
            <P>Content <SU>99</SU><FTREF />2</P>
            <P>Content <E T="03">Emph</E></P>
        </ROOT>"""
        sxs = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = build_section_by_section(sxs, '99', 939)
        self.assertEqual(1, len(structures))
        self.assertEqual(structures[0], {
            'title': 'Section 99.3 Info',
            'label': '99-3',
            'page': 939,
            'paragraphs': ['Content 1', 'Content  2',
                           'Content <em data-original="E-03">Emph</em>'],
            'children': []
        })

    def test_build_section_by_section_same_level(self):
        """Check that labels are being added correctly"""
        xml = """
        <ROOT>
            <HD SOURCE="HD2">Section 99.3 Something Here</HD>
            <HD SOURCE="HD3">3(q)(4) More Info</HD>
            <P>Content 1</P>
            <HD SOURCE="HD3">Subheader, Really</HD>
            <P>Content 2</P>
        </ROOT>"""
        sxs = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = build_section_by_section(sxs, '99', 765)
        self.assertEqual(1, len(structures))
        self.assertEqual(structures[0], {
            'title': 'Section 99.3 Something Here',
            'label': '99-3',
            'paragraphs': [],
            'page': 765,
            'children': [{
                'title': '3(q)(4) More Info',
                'label': '99-3-q-4',
                'paragraphs': ['Content 1'],
                'page': 765,
                'children': [{
                    'title': 'Subheader, Really',
                    'paragraphs': ['Content 2'],
                    'children': [],
                    'page': 765
                }]
            }]
        })

    def test_build_section_by_section_emphasis(self):
        xml = """
        <ROOT>
            <HD SOURCE="H2">Section 876.23 Title Here</HD>
            <P>This sentence has<E T="03">emphasis</E>!</P>
            <P>Non emph,<E T="03">emph</E>then more.</P>
            <P>This one has an <E T="03">emph</E> with spaces.</P>
        </ROOT>"""
        sxs = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = build_section_by_section(sxs, '876', 23)
        paragraphs = structures[0]['paragraphs']
        self.assertEqual(paragraphs, [
            'This sentence has <em data-original="E-03">emphasis</em>!',
            'Non emph, <em data-original="E-03">emph</em> then more.',
            'This one has an <em data-original="E-03">emph</em> with spaces.'
        ])

    def test_split_into_ttsr(self):
        xml = """
        <ROOT>
            <HD SOURCE="HD3">Section Header</HD>
            <P>Content 1</P>
            <P>Content 2</P>
            <HD SOURCE="HD4">Sub Section Header</HD>
            <P>Content 3</P>
            <HD SOURCE="HD4">Another</HD>
            <P>Content 4</P>
            <HD SOURCE="HD3">Next Section</HD>
            <P>Content 5</P>
        </ROOT>"""
        sxs = list(etree.fromstring(xml).xpath("/ROOT/*"))
        title, text_els, sub_sects, remaining = split_into_ttsr(sxs)
        self.assertEqual("Section Header", title.text)
        self.assertEqual(2, len(text_els))
        self.assertEqual("Content 1", text_els[0].text)
        self.assertEqual("Content 2", text_els[1].text)
        self.assertEqual(4, len(sub_sects))
        self.assertEqual("Sub Section Header", sub_sects[0].text)
        self.assertEqual("Content 3", sub_sects[1].text)
        self.assertEqual("Another", sub_sects[2].text)
        self.assertEqual("Content 4", sub_sects[3].text)
        self.assertEqual(2, len(remaining))
        self.assertEqual("Next Section", remaining[0].text)
        self.assertEqual("Content 5", remaining[1].text)

    def test_add_spaces_to_title(self):
        """Account for wonky titles without proper spacing"""
        self.assertEqual('Section 101.23 Some Title',
                         add_spaces_to_title('Section 101.23 Some Title'))
        self.assertEqual('Section 101.23 Some Title',
                         add_spaces_to_title('Section 101.23Some Title'))
        self.assertEqual('Section 101.23:Some Title',
                         add_spaces_to_title('Section 101.23:Some Title'))
        self.assertEqual('Appendix A-Some Title',
                         add_spaces_to_title('Appendix A-Some Title'))
        self.assertEqual('Comment 29(b)(1)-1 Some Title',
                         add_spaces_to_title('Comment 29(b)(1)-1Some Title'))

    def test_parse_into_label(self):
        self.assertEqual("101-22",
                         parse_into_label("Section 101.22Stuff", "101"))
        self.assertEqual("101-22-d",
                         parse_into_label("22(d) Content", "101"))
        self.assertEqual("101-22-d-5",
                         parse_into_label("22(d)(5) Content", "101"))
        self.assertEqual("101-22-d-5-x",
                         parse_into_label("22(d)(5)(x) Content", "101"))
        self.assertEqual("101-22-d-5-x",
                         parse_into_label(u"§ 101.22(d)(5)(x) Content", "101"))
        self.assertEqual("101-22-d-5-x-Q",
                         parse_into_label("22(d)(5)(x)(Q) Content", "101"))
        self.assertEqual("101-A",
                         parse_into_label("Appendix A Heading", "101"))
        self.assertEqual("101-21-c-Interp-1",
                         parse_into_label("Comment 21(c)-1 Heading", "101"))

        self.assertEqual(None,
                         parse_into_label("Application of this rule", "101"))

    def test_is_child_of(self):
        parent = """<HD SOURCE="H2">Section 22.1</HD>"""
        parent = etree.fromstring(parent)

        child = """<P>Something</P>"""
        self.assertTrue(is_child_of(etree.fromstring(child), parent))

        child = """<HD SOURCE="H3">Something</HD>"""
        self.assertTrue(is_child_of(etree.fromstring(child), parent))

        child = """<HD SOURCE="H1">Section 22.2</HD>"""
        self.assertFalse(is_child_of(etree.fromstring(child), parent))

        child = """<HD SOURCE="H2">Header without Citation</HD>"""
        self.assertTrue(is_child_of(etree.fromstring(child), parent))

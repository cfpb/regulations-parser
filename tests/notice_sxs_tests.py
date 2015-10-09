# vim: set encoding=utf-8
from lxml import etree
from regparser.notice import sxs
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
            self.assertEqual(332, sxs.find_page(xml, l, 332))
        for l in range(6, 10):
            self.assertEqual(333, sxs.find_page(xml, l, 332))
        for l in range(10, 15):
            self.assertEqual(334, sxs.find_page(xml, l, 332))

    def test_find_section_by_section(self):
        sxs_xml = """
            <HD SOURCE="HD2">Sub Section</HD>
            <P>Content</P>
            <HD SOURCE="HD3">Sub sub section</HD>
            <EXTRACT><P>This is in an extract</P></EXTRACT>
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

        #   Must use text field since the nodes are not directly comparable
        sxs_texts = ['Sub Section', 'Content', 'Sub sub section',
                     'This is in an extract', 'Sub Sub Content']

        computed = sxs.find_section_by_section(etree.fromstring(full_xml))
        self.assertEqual(sxs_texts, map(lambda el: el.text, computed))

    def test_find_section_by_section_intro_text(self):
        sxs_xml = """
            <P>Some intro text</P>
            <P>This text includes a reference to Section 8675.309(a)</P>
            <HD SOURCE="HD2">Section 8675.309 Stuff</HD>
            <P>Content</P>"""
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

        sxs_texts = ['Section 8675.309 Stuff', 'Content']
        computed = sxs.find_section_by_section(etree.fromstring(full_xml))
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
        self.assertEqual([], sxs.find_section_by_section(etree.fromstring(
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
            <FP>Content 6</FP>
        </ROOT>"""
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 83, '100')
        self.assertEqual(2, len(structures))
        self.assertEqual(structures[0], {
            'title': 'Section Header',
            'paragraphs': [
                'Content 1',
                'Content 2'
                ],
            'footnote_refs': [],
            'children': [
                {
                    'title': 'Sub Section Header',
                    'paragraphs': ['Content 3'],
                    'children': [],
                    'footnote_refs': [],
                    'page': 83
                },
                {
                    'title': 'Another',
                    'paragraphs': ['Content 4'],
                    'children': [],
                    'footnote_refs': [],
                    'page': 83
                }],
            'page': 83
            })
        self.assertEqual(structures[1], {
            'title': '4(b) Header',
            'paragraphs': ['Content 5', 'Content 6'],
            'labels': ['100-4-b'],
            'page': 83,
            'footnote_refs': [],
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
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 21, '100')
        self.assertEqual(1, len(structures))
        self.assertEqual(structures[0], {
            'title': 'Section Header',
            'paragraphs': [
                'Content 1',
                'Content 2',
                ],
            'children': [],
            'footnote_refs': [],
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
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 2323, '99')
        self.assertEqual(1, len(structures))
        self.assertEqual(structures[0], {
            'title': 'Section 99.3 Info',
            'labels': ['99-3'],
            'paragraphs': ['Content 1'],
            'page': 2323,
            'footnote_refs': [],
            'children': [{
                'title': '3(q)(4) More Info',
                'labels': ['99-3-q-4'],
                'paragraphs': ['Content 2'],
                'page': 2323,
                'footnote_refs': [],
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
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 939, '99')
        self.assertEqual(1, len(structures))
        self.assertEqual(structures[0], {
            'title': 'Section 99.3 Info',
            'labels': ['99-3'],
            'page': 939,
            'paragraphs': ['Content 1', 'Content 2',
                           'Content <em data-original="E-03">Emph</em>'],
            'footnote_refs': [{'paragraph': 1,
                               'reference': '99',
                               'offset': 8}],
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
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 765, '99')
        self.assertEqual(1, len(structures))
        self.assertEqual(structures[0], {
            'title': 'Section 99.3 Something Here',
            'labels': ['99-3'],
            'paragraphs': [],
            'page': 765,
            'footnote_refs': [],
            'children': [{
                'title': '3(q)(4) More Info',
                'labels': ['99-3-q-4'],
                'paragraphs': ['Content 1'],
                'page': 765,
                'footnote_refs': [],
                'children': [{
                    'title': 'Subheader, Really',
                    'paragraphs': ['Content 2'],
                    'footnote_refs': [],
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
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 23, '876')
        paragraphs = structures[0]['paragraphs']
        self.assertEqual(paragraphs, [
            'This sentence has <em data-original="E-03">emphasis</em>!',
            'Non emph, <em data-original="E-03">emph</em> then more.',
            'This one has an <em data-original="E-03">emph</em> with spaces.'
        ])

    def test_build_section_by_section_footnotes_full(self):
        xml = """
        <ROOT>
            <HD SOURCE="H2">Section 876.23 Title Here</HD>
            <P>Sometimes<E T="03">citations</E><SU>5</SU><FTREF /></P>
            <P>Are rather complicated</P>
            <FTNT><P><SU>5</SU>Footnote contents</P></FTNT>
        </ROOT>"""
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 23, '876')
        sometimes_txt = 'Sometimes <em data-original="E-03">citations</em>'
        self.assertEqual(structures[0]['paragraphs'], [
            sometimes_txt, 'Are rather complicated'
        ])
        self.assertEqual(structures[0]['footnote_refs'],
                         [{'paragraph': 0,
                           'reference': '5',
                           'offset': len(sometimes_txt)}])

    def test_build_section_by_section_multiple(self):
        xml = """
        <ROOT>
            <HD SOURCE="H2">Comments 22(a)-5, 22(a)-6, and 22(b)</HD>
            <P>Content</P>
        </ROOT>"""
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 23, '876')
        self.assertEqual(len(structures), 1)
        self.assertEqual(structures[0]['labels'],
                         ['876-22-a-Interp-5', '876-22-a-Interp-6',
                          '876-22-b-Interp'])

    def test_build_section_by_section_repeat_label(self):
        xml = """
        <ROOT>
            <HD SOURCE="H2">This references 23(c)</HD>
            <P>Content 1</P>
            <HD SOURCE="H3">SO DOES THIS! 23(c) continued</HD>
            <P>Content 2</P>
        </ROOT>"""
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 23, '876')
        self.assertEqual(len(structures), 1)
        struct1 = structures[0]
        self.assertEqual(struct1['labels'], ['876-23-c'])
        self.assertEqual(['Content 1'], struct1['paragraphs'])
        self.assertEqual(len(struct1['children']), 1)
        struct2 = struct1['children'][0]
        self.assertEqual(['Content 2'], struct2['paragraphs'])
        self.assertFalse('labels' in struct2)

        # Now the same, but on the same H level
        xml = """
        <ROOT>
            <HD SOURCE="H2">This references 23(c)</HD>
            <P>Content 1</P>
            <HD SOURCE="H2">SO DOES THIS! 23(c) continued</HD>
            <P>Content 2</P>
        </ROOT>"""
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 23, '876')
        self.assertEqual(len(structures), 1)
        struct1 = structures[0]
        self.assertEqual(struct1['labels'], ['876-23-c'])
        self.assertEqual(['Content 1'], struct1['paragraphs'])
        self.assertEqual(len(struct1['children']), 1)
        struct2 = struct1['children'][0]
        self.assertEqual(['Content 2'], struct2['paragraphs'])
        self.assertFalse('labels' in struct2)

        # Semi-repeated
        xml = """
        <ROOT>
            <HD SOURCE="H2">Appendices A and B</HD>
            <P>Content 1</P>
            <HD SOURCE="H2">Appendix B</HD>
            <P>Content 2</P>
        </ROOT>"""
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 23, '876')
        self.assertEqual(len(structures), 1)
        struct1 = structures[0]
        self.assertEqual(struct1['labels'], ['876-A', '876-B'])
        self.assertEqual(['Content 1'], struct1['paragraphs'])
        self.assertEqual(len(struct1['children']), 1)
        struct2 = struct1['children'][0]
        self.assertEqual(['Content 2'], struct2['paragraphs'])
        self.assertFalse('labels' in struct2)

    def test_build_section_by_section_backtrack(self):
        xml = """
        <ROOT>
            <HD SOURCE="H2">This references 23(c)(3)</HD>
            <P>Content 1</P>
            <HD SOURCE="H2">Off handed comment about 23(c)</HD>
            <P>Content 2</P>
        </ROOT>"""
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 23, '876')
        self.assertEqual(len(structures), 1)
        struct1 = structures[0]
        self.assertEqual(struct1['labels'], ['876-23-c-3'])
        self.assertEqual(['Content 1'], struct1['paragraphs'])
        self.assertEqual(len(struct1['children']), 1)
        struct2 = struct1['children'][0]
        self.assertEqual(['Content 2'], struct2['paragraphs'])
        self.assertFalse('labels' in struct2)

        # Same, but deeper H level
        xml = """
        <ROOT>
            <HD SOURCE="H2">This references 23(c)(3)</HD>
            <P>Content 1</P>
            <HD SOURCE="H3">Off handed comment about 23(c)</HD>
            <P>Content 2</P>
        </ROOT>"""
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 23, '876')
        self.assertEqual(len(structures), 1)
        struct1 = structures[0]
        self.assertEqual(struct1['labels'], ['876-23-c-3'])
        self.assertEqual(['Content 1'], struct1['paragraphs'])
        self.assertEqual(len(struct1['children']), 1)
        struct2 = struct1['children'][0]
        self.assertEqual(['Content 2'], struct2['paragraphs'])
        self.assertFalse('labels' in struct2)

        # No part then part
        xml = """
        <ROOT>
            <HD SOURCE="H3">This references 23(c)</HD>
            <HD SOURCE="H3">Off handed comment about section 1111.23</HD>
            <P>Content 2</P>
        </ROOT>"""
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 22, '1111')
        self.assertEqual(len(structures), 1)
        struct1 = structures[0]
        self.assertEqual(struct1['labels'], ['1111-23-c'])
        self.assertEqual([], struct1['paragraphs'])
        self.assertEqual(len(struct1['children']), 1)
        struct2 = struct1['children'][0]
        self.assertEqual(['Content 2'], struct2['paragraphs'])
        self.assertFalse('labels' in struct2)

    def test_build_section_by_section_different_part(self):
        xml = """
        <ROOT>
            <HD SOURCE="H2">This references Section 1111.23(c)(3)</HD>
            <P>Content 1</P>
            <HD SOURCE="H2">This one's about 24(c)</HD>
            <P>Content 2</P>
        </ROOT>"""
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 23, '876')
        self.assertEqual(len(structures), 2)
        struct1, struct2 = structures
        self.assertEqual(struct1['labels'], ['1111-23-c-3'])
        self.assertEqual(['Content 1'], struct1['paragraphs'])
        self.assertEqual(len(struct1['children']), 0)

        self.assertEqual(struct2['labels'], ['1111-24-c'])
        self.assertEqual(['Content 2'], struct2['paragraphs'])
        self.assertEqual(len(struct2['children']), 0)

        # Same, but deeper H level
        xml = """
        <ROOT>
            <HD SOURCE="H2">This references 23(c)(3)</HD>
            <P>Content 1</P>
            <HD SOURCE="H3">Off handed comment about 23(c)</HD>
            <P>Content 2</P>
        </ROOT>"""
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 23, '876')
        self.assertEqual(len(structures), 1)
        struct1 = structures[0]
        self.assertEqual(struct1['labels'], ['876-23-c-3'])
        self.assertEqual(['Content 1'], struct1['paragraphs'])
        self.assertEqual(len(struct1['children']), 1)
        struct2 = struct1['children'][0]
        self.assertEqual(['Content 2'], struct2['paragraphs'])
        self.assertFalse('labels' in struct2)

    def test_build_section_by_section_dup_child(self):
        xml = """
        <ROOT>
            <HD SOURCE="H2">References 31(a) and (b)</HD>
            <P>Content 1</P>
            <HD SOURCE="H3">Subcontent</HD>
            <P>Content 2</P>
            <HD SOURCE="H3">References 31(b)(1)</HD>
            <P>Content 3</P>
        </ROOT>"""
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        structures = sxs.build_section_by_section(sxs_lst, 23, '876')
        self.assertEqual(len(structures), 1)
        struct1 = structures[0]
        self.assertEqual(struct1['labels'], ['876-31-a', '876-31-b'])
        self.assertEqual(['Content 1'], struct1['paragraphs'])
        self.assertEqual(len(struct1['children']), 2)
        struct1_h, struct2 = struct1['children']

        self.assertEqual(struct1_h['title'], 'Subcontent')
        self.assertEqual(['Content 2'], struct1_h['paragraphs'])
        self.assertEqual(len(struct1_h['children']), 0)

        self.assertEqual(struct2['labels'], ['876-31-b-1'])
        self.assertEqual(['Content 3'], struct2['paragraphs'])
        self.assertEqual(len(struct2['children']), 0)

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
        sxs_lst = list(etree.fromstring(xml).xpath("/ROOT/*"))
        title, text_els, sub_sects, remaining = sxs.split_into_ttsr(sxs_lst,
                                                                    '1111')
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
                         sxs.add_spaces_to_title('Section 101.23 Some Title'))
        self.assertEqual('Section 101.23 Some Title',
                         sxs.add_spaces_to_title('Section 101.23Some Title'))
        self.assertEqual('Section 101.23:Some Title',
                         sxs.add_spaces_to_title('Section 101.23:Some Title'))
        self.assertEqual('Appendix A-Some Title',
                         sxs.add_spaces_to_title('Appendix A-Some Title'))
        self.assertEqual(
            'Comment 29(b)(1)-1 Some Title',
            sxs.add_spaces_to_title('Comment 29(b)(1)-1Some Title'))

    def test_parse_into_labels(self):
        self.assertEqual(["101-22"],
                         sxs.parse_into_labels("Section 101.22Stuff", "101"))
        self.assertEqual(["101-22-d"],
                         sxs.parse_into_labels("22(d) Content", "101"))
        self.assertEqual(["101-22-d-5"],
                         sxs.parse_into_labels("22(d)(5) Content", "101"))
        self.assertEqual(["101-22-d-5-x"],
                         sxs.parse_into_labels("22(d)(5)(x) Content", "101"))
        self.assertEqual(
            ["101-22-d-5-x"],
            sxs.parse_into_labels(u"§ 101.22(d)(5)(x) Content", "101"))
        self.assertEqual(
            ["101-22-d-5-x-Q"],
            sxs.parse_into_labels("22(d)(5)(x)(Q) Content", "101"))
        self.assertEqual(["101-A"],
                         sxs.parse_into_labels("Appendix A Heading", "101"))
        self.assertEqual(
            ["101-21-c-Interp-1"],
            sxs.parse_into_labels("Comment 21(c)-1 Heading", "101"))
        text = u'Official Interpretations of § 101.33(c)(2)'
        self.assertEqual(['101-33-c-2-Interp'],
                         sxs.parse_into_labels(text, '101'))
        text = 'Comments 33(a)-8 and 33(a)-9'
        self.assertEqual(['101-33-a-Interp-8', '101-33-a-Interp-9'],
                         sxs.parse_into_labels(text, '101'))

        self.assertEqual(
            [],
            sxs.parse_into_labels("Application of this rule", "101"))
        text = 'Section 1111.39Content content 1111.39(d) Exeptions'
        self.assertEqual(['1111-39', '1111-39-d'],
                         sxs.parse_into_labels(text, '101'))

        text = "Appendix H—Closed-End Model Forms and Clauses-7(i)"
        self.assertEqual(['101-H'], sxs.parse_into_labels(text, '101'))

    def test_is_child_of(self):
        parent = """<HD SOURCE="H2">Section 22.1</HD>"""
        parent = etree.fromstring(parent)

        child = """<P>Something</P>"""
        self.assertTrue(
            sxs.is_child_of(etree.fromstring(child), parent, '1111'))

        child = """<HD SOURCE="H3">Something</HD>"""
        self.assertTrue(
            sxs.is_child_of(etree.fromstring(child), parent, '1111'))

        child = """<HD SOURCE="H1">Section 22.2</HD>"""
        self.assertFalse(
            sxs.is_child_of(etree.fromstring(child), parent, '1111'))

        child = """<HD SOURCE="H2">Header without Citation</HD>"""
        self.assertTrue(
            sxs.is_child_of(etree.fromstring(child), parent, '1111'))

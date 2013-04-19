from parser.tree.interpretation.carving import *
from unittest import TestCase

class EmptyClass: pass


class DepthInterpretationCarvingTest(TestCase):

    def header(self, p1):
        h = EmptyClass()
        h.keyterm = ""
        h.whole = ""
        paragraph1 = EmptyClass()
        paragraph1.id = p1
        h.paragraph1 = paragraph1
        h.paragraph2 = ""
        h.paragraph3 = ""
        h.paragraph4 = ""
        return h

    def test_find_next_section_offsets(self):
        section_5 = "Section 201.5\nSection 202.3\nother body\n\n"
        section_65 = "Section 201.65\n body body\n\nSection Other"
        text = "Something Section\n" + section_5 + section_65
        self.assertEqual(None, find_next_section_offsets(text, 404))

        begin,end = find_next_section_offsets(text, 201)
        self.assertEqual(section_5, text[begin:end])

    def test_sections(self):
        section_5 = "Section 201.5\nSection 202.3\nother body\n\n"
        section_65 = "Section 201.65\n body body\n\nSection Other"
        text = "Something Section\n" + section_5 + section_65
        self.assertEqual([], sections(text,404))

        interps = sections(text, 201)
        self.assertEqual(2, len(interps))
        begin, end = interps[0]
        self.assertEqual(section_5, text[begin:end])
        begin, end = interps[1]
        self.assertEqual(section_65, text[begin:end])

    def test_get_section_number(self):
        self.assertEqual("101", 
                get_section_number("Section 55.101 Something Here", 55))

    def test_find_next_appendix_offsets(self):
        part1 = "This is \nAppendix Q - Some title\nBody body\n"
        part2 = "Appendix B - Another\nThe reckoning."
        self.assertEqual((9, len(part1)), 
                find_next_appendix_offsets(part1 + part2))

    def test_appendices(self):
        part0 = "Something something\n"
        app1 = "Appendix R - Some title\nThen some\nbody content here\n"
        app2 = "Appendix M - Another\nContent content\n"
        app3 = "Appendix L - Once more\nAppendix not\n"
        self.assertEqual([
            (len(part0), len(part0+app1)), 
            (len(part0+app1), len(part0+app1+app2)),
            (len(part0+app1+app2), len(part0+app1+app2+app3))
            ], appendices(part0 + app1 + app2 + app3))

    def test_get_appendix_letter(self):
        self.assertEqual("M", get_appendix_letter("Appendix M - More Info"))

    def test_applicable_offsets_paragraphs(self):
        p4_text = "Paragraph 4(z)\nParagraph Invalid\n"
        text = "Paragraph 3(b)(c)\n\n\n" + p4_text
        self.assertEqual([], applicable_offsets(text, 2))

        three = applicable_offsets(text, 3)
        self.assertEqual(1, len(three))
        start, end = three[0]
        self.assertEqual(text, text[start:end])

        four = applicable_offsets(text, 4)
        self.assertEqual(1, len(four))
        start, end = four[0]
        self.assertEqual(p4_text, text[start:end])

    def test_applicable_offsets_keywords(self):
        p3_kw1_text = "3(b)(1)(iv)(Z) Some Definition\n"
        p3_kw2_text = "3(i) Another\n3 none\n"
        text = "Blah 3(b)(c)\n\n" + p3_kw1_text + p3_kw2_text
        self.assertEqual([], applicable_offsets(text, 4))

        three = applicable_offsets(text, 3)
        self.assertEqual(2, len(three))
        start, end = three[0]
        self.assertEqual(p3_kw1_text, text[start:end])
        start, end = three[1]
        self.assertEqual(p3_kw2_text, text[start:end])

    def test_applicable_offsets_mix(self):
        p1_text = "Paragraph 3(b)(1)\n\n"
        p2_text = "3(b)(1)(iv)(Z) Some Definition\n"
        p3_text = "3(i) Another\n3 a\n"
        text = p1_text + p2_text + p3_text
        self.assertEqual([], applicable_offsets(text, 4))

        three = applicable_offsets(text, 3)
        self.assertEqual(3, len(three))

        self.assertEqual([p1_text, p2_text, p3_text], 
                [text[start:end] for start, end in three])

    def test_build_label_immutable(self):
        label = "Some label"
        build_label(label, self.header('a'))
        self.assertEqual("Some label", label)

    def test_build_label_p_depth(self):
        prefix = "104.22"
        self.assertEqual(prefix + "(a)", 
                build_label(prefix, self.header('a')))

        match = self.header('b')
        match.paragraph2 = EmptyClass()
        match.paragraph2.id = '3'
        self.assertEqual(prefix + "(b)(3)", build_label(prefix, match))

        match.paragraph3 = EmptyClass()
        match.paragraph3.id = 'iv'
        match.paragraph4 = EmptyClass()
        match.paragraph4.id = 'E'
        self.assertEqual(prefix + "(b)(3)(iv)(E)", build_label(prefix, match))

    def test_applicable_paragraph_none(self):
        text = "No paragraph here\n"
        self.assertEqual(None, applicable_paragraph(text, 101))

    def test_applicable_paragraph_paragraphs(self):
        text = "Paragraph 3(b)\n"
        self.assertEqual(None, applicable_paragraph(text, 1))

        three = applicable_paragraph(text, 3)
        self.assertEqual('', three.keyterm)
        self.assertNotEqual('', three.whole)
        self.assertEqual('b', three.paragraph1.id)
        self.assertEqual('', three.paragraph2)

    def test_applicable_paragraph_keywords(self):
        text = "3(b)(1)(iv)(Z) Some Definition\n"

        three = applicable_paragraph(text, 3)

        self.assertEqual('', three.whole)
        self.assertNotEqual('', three.keyterm)
        self.assertEqual('Some Definition', three.keyterm.term.strip())
        self.assertEqual('b', three.paragraph1.id)
        self.assertEqual('1', three.paragraph2.id)
        self.assertEqual('iv', three.paragraph3.id)
        self.assertEqual('Z', three.paragraph4.id)

    def test_applicable_paragraph_nonewline(self):
        text = "Paragraph 4(b)(3)(i)"
        self.assertEqual(str(applicable_paragraph(text + "\n", 4)), 
                str(applicable_paragraph(text, 4)))

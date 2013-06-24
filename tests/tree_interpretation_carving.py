from parser.tree.interpretation.carving import *
from unittest import TestCase

class EmptyClass: pass


class DepthInterpretationCarvingTest(TestCase):

    def header(self, p1):
        """Creates a mock match object for paragraph heading parsing"""
        h = EmptyClass()
        h.section = '22'
        h.pars = EmptyClass()
        h.pars.level1 = p1
        h.pars.level2 = ""
        h.pars.level3 = ""
        h.pars.level4 = ""
        return h

    def test_segment_by_header(self):
        text = "Interp interp\n"
        s22 = "Section 87.22Some Title\nSome content\n"
        s23 = "Paragraph 23(b)(4)(v)(Z)\nPar par\n"
        s25 = "Section 87.25 Title\nEven more info here\n"
        sb = "Appendix B-Some Title\nContent content\n"
        self.assertEqual([(len(text), len(text + s22)),
            (len(text+s22), len(text+s22+s23)), 
            (len(text+s22+s23), len(text+s22+s23+s25)),
            (len(text+s22+s23+s25), len(text+s22+s23+s25+sb))
            ], segment_by_header(text + s22 + s23 + s25 + sb, 87))

    def test_segment_by_header_ten(self):
        text = "Interp interp\n"
        s10a = "10(a) Some Content\n\n"
        s10a1 = "10(a)(1) Some subcontent\nContent content\n"
        s10b = "10(b) Second level paragraph\nContennnnnt"

        self.assertEqual(3, len(segment_by_header(text+s10a+s10a1+s10b, 0)))

    def test_get_section_number(self):
        self.assertEqual("101", 
                get_section_number("Section 55.101 Something Here", 55))

    def test_get_appendix_letter(self):
        self.assertEqual("M", get_appendix_letter("Appendix M - More Info"))

    def test_build_label_immutable(self):
        label = "Some label"
        build_label(label, self.header('a'))
        self.assertEqual("Some label", label)

    def test_build_label_p_depth(self):
        prefix = "104-"
        self.assertEqual(prefix + "22(a)", 
                build_label(prefix, self.header('a')))

        match = self.header('b')
        match.pars.level2 = '3'
        self.assertEqual(prefix + "22(b)(3)", build_label(prefix, match))

        match.pars.level3 = 'iv'
        match.pars.level4 = 'E'
        self.assertEqual(prefix + "22(b)(3)(iv)(E)", 
                build_label(prefix, match))

    def test_applicable_paragraph_none(self):
        text = "No paragraph here\n"
        self.assertEqual(None, applicable_paragraph(text))

    def test_applicable_paragraph_paragraphs(self):
        text = "Paragraph 3(b)\n"
        three = applicable_paragraph(text)
        self.assertEqual('b', three.pars.level1)
        self.assertEqual('', three.pars.level2)

    def test_applicable_paragraph_keywords(self):
        text = "3(b)(1)(iv)(Z) Some Definition\n"

        three = applicable_paragraph(text)

        self.assertEqual('Some Definition', three.term.strip())
        self.assertEqual('b', three.pars.level1)
        self.assertEqual('1', three.pars.level2)
        self.assertEqual('iv', three.pars.level3)
        self.assertEqual('Z', three.pars.level4)

    def test_applicable_paragraph_nonewline(self):
        text = "Paragraph 4(b)(3)(i)"
        self.assertEqual(str(applicable_paragraph(text + "\n")), 
                str(applicable_paragraph(text)))

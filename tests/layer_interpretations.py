from reg_parser.layer.interpretations import Interpretations
from reg_parser.tree import struct
from unittest import TestCase

class LayerInterpretationTest(TestCase):

    def test_regtext_to_interp_label(self):
        self.assertEqual(None,
            Interpretations.regtext_to_interp_label(['100']))
        self.assertEqual(['100', 'Interpretations', '4'],
            Interpretations.regtext_to_interp_label(['100', '4']))
        self.assertEqual(['100', 'Interpretations', 'C'],
            Interpretations.regtext_to_interp_label(['100', 'C']))
        self.assertEqual(['100', 'Interpretations', '7(b)(4)(i)'],
            Interpretations.regtext_to_interp_label(['100', '7', 'b', '4',
                'i']))
        self.assertEqual(['100', 'Interpretations', 'Z7.iv.R'],
            Interpretations.regtext_to_interp_label(['100', 'Z', '7', 'iv',
                'R']))

    def test_regtext_label(self):
        interp = Interpretations(None)
        self.assertEqual('(c)', interp.regtext_label(['c']))
        self.assertEqual('(q)(X)(_)', interp.regtext_label(['q', 'X', '_']))
        self.assertEqual('(a)(2)(i)(A)', 
                interp.regtext_label(['a', '2', 'i', 'A']))

    def test_appendix_label(self):
        interp = Interpretations(None)
        self.assertEqual('5', interp.appendix_label(['5']))
        self.assertEqual('5.ii.Q', interp.appendix_label(['5', 'ii', 'Q']))

    def test_process(self):
        root = struct.node(children = [
            struct.node("Interp11a", 
                [struct.node("child1"), struct.node("child2")],
                struct.label("102-Interpretations-11(a)")),
            struct.node("Interp11c5v",
                label=struct.label("102-Interpretations-11(c)(5)(v)")),
            struct.node("InterpB5ii",
                label=struct.label("102-Interpretations-B5.ii")),
            struct.node(children=[struct.node(children=[
                struct.node("Interp9c1",
                    label=struct.label("102-Interpretations-9(c)(1)"))])])
                ], label=struct.label("102", ["102"]))

        interp = Interpretations(root)
        interp11a = interp.process(struct.node(
            label=struct.label("", ["102", "11", "a"])))
        interp11c5v = interp.process(struct.node(
            label=struct.label("", ["102", "11", "c", "5", "v"])))
        interpB5ii = interp.process(struct.node(
            label=struct.label("", ["102", "B", "5", "ii"])))
        interp9c1 = interp.process(struct.node(
            label=struct.label("", ["102", "9", "c", "1"])))
        
        self.assertEqual(1, len(interp11a))
        self.assertEqual(1, len(interp11c5v))
        self.assertEqual(1, len(interpB5ii))
        self.assertEqual(1, len(interp9c1))
        self.assertEqual("102-Interpretations-11(a)",
            interp11a[0]['reference'])
        self.assertEqual("102-Interpretations-11(c)(5)(v)",
            interp11c5v[0]['reference'])
        self.assertEqual("102-Interpretations-B5.ii",
            interpB5ii[0]['reference'])
        self.assertEqual("102-Interpretations-9(c)(1)",
            interp9c1[0]['reference'])
        self.assertEqual("Interp11achild1child2", interp11a[0]['text'])
        self.assertEqual("Interp9c1", interp9c1[0]['text'])
        self.assertEqual(None, interp.process(struct.node(
            label=struct.label("", ["102", "10", "a"]))))

    def test_process_subparagraph_of_referenced_text(self):
        root = struct.node(children = [
            struct.node("\n\n\n", [   #   Empty
                struct.node("Interp11a1", [],
                    struct.label(
                        "100-Interpretations-11(a)(1)", title="11(a)(1)"
                    )
                )
            ], struct.label("100-Interpretations-11(a)"))
        ], label=struct.label("100", ["100"]))
        interp = Interpretations(root)
        self.assertEqual(None, interp.process(struct.node(
            label=struct.label("", ["100", "11", "a"]))))
        self.assertFalse(interp.process(struct.node(
            label=struct.label("", ["100", "11", "a", "1"]))) is None)

    def test_process_has_multiple_paragraphs(self):
        root = struct.node(children = [
            struct.node("\n\n\n", [   #   Empty
                struct.node("Interp11a-1", [],
                    struct.label("100-Interpretations-11(a)-1"))
                ], struct.label("100-Interpretations-11(a)"))
            ], label=struct.label("100", ["100"]))
        interp = Interpretations(root)
        self.assertFalse(interp.process(struct.node(
            label=struct.label("", ["100", "11", "a"]))) is None)

    def test_empty_interpretations(self):
        interp = Interpretations(None)
        self.assertTrue(interp.empty_interpretation(struct.node('\n\n',
            [])))
        self.assertTrue(interp.empty_interpretation(struct.node('\n\n',
            [struct.node('SubSection', [], struct.label('', [], 'Title'))])))
        self.assertFalse(interp.empty_interpretation(struct.node('Content',
            [])))
        self.assertFalse(interp.empty_interpretation(struct.node('',
            [struct.node('Subpar', [])])))

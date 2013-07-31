from regparser.layer.interpretations import Interpretations
from regparser.tree import struct
from unittest import TestCase

class LayerInterpretationTest(TestCase):

    def test_process(self):
        root = struct.Node(children = [
            struct.Node("Interp11a", 
                [struct.Node("child1"), struct.Node("child2")],
                ['102', '11', 'a', 'Interp']),
            struct.Node("Interp11c5v", 
                label=['102', '11', 'c', '5', 'v', 'Interp']),
            struct.Node("InterpB5ii", label=['102','B','5','ii','Interp']),
            struct.Node(children=[struct.Node(children=[
                struct.Node("Interp9c1", label=['102','9','c','1','Interp'])
                ], label=['102'])])
        ])

        interp = Interpretations(root)
        interp11a = interp.process(struct.Node(label=['102', '11', 'a']))
        interp11c5v = interp.process(struct.Node(
            label=['102', '11', 'c', '5', 'v']
        ))
        interpB5ii = interp.process(struct.Node(label=['102','B','5','ii']))
        interp9c1 = interp.process(struct.Node(label=['102', '9', 'c', '1']))
        
        self.assertEqual(1, len(interp11a))
        self.assertEqual(1, len(interp11c5v))
        self.assertEqual(1, len(interpB5ii))
        self.assertEqual(1, len(interp9c1))
        self.assertEqual('102-11-a-Interp', interp11a[0]['reference'])
        self.assertEqual('102-11-c-5-v-Interp', interp11c5v[0]['reference'])
        self.assertEqual('102-B-5-ii-Interp', interpB5ii[0]['reference'])
        self.assertEqual('102-9-c-1-Interp', interp9c1[0]['reference'])
        self.assertEqual("Interp11achild1child2", interp11a[0]['text'])
        self.assertEqual("Interp9c1", interp9c1[0]['text'])
        self.assertEqual(None, interp.process(struct.Node(
            label=["102", "10", "a"])))

    def test_process_subparagraph_of_referenced_text(self):
        root = struct.Node(children = [
            struct.Node("\n\n\n", [   #   Empty
                struct.Node("Interp11a1", label=['100','11','a','1','Interp'])
            ], label=['100', '11', 'a', 'Interp'])
        ], label=['100'])
        interp = Interpretations(root)
        self.assertEqual(None, interp.process(struct.Node(
            label=['100', '11', 'a']
        )))
        self.assertFalse(interp.process(struct.Node(
            label=['100', '11', 'a', '1'])) is None)

    def test_process_has_multiple_paragraphs(self):
        root = struct.Node(children = [
            struct.Node("\n\n\n", [   #   Empty
                struct.Node("Interp11a-1",
                    label=['100','11','a','Interp','1'])
                ], ['100', '11', 'a', 'Interp'])
            ], label=['100'])
        interp = Interpretations(root)
        self.assertFalse(interp.process(struct.Node(
            label=["100", "11", "a"])) is None)

    def test_empty_interpretations(self):
        interp = Interpretations(None)
        self.assertTrue(interp.empty_interpretation(struct.Node('\n\n')))
        self.assertTrue(interp.empty_interpretation(struct.Node('',
            [struct.Node('Subpar')])))
        self.assertFalse(interp.empty_interpretation(struct.Node('Content')))
        self.assertFalse(interp.empty_interpretation(struct.Node('',
            [struct.Node('Something', label=['1', 'Interp', '3'])])))

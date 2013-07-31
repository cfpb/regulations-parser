from unittest import TestCase

from regparser.layer.paragraph_markers import ParagraphMarkers
from regparser.tree.struct import Node

class ParagraphMarkersTest(TestCase):

    def test_process_no_results(self):
        pm = ParagraphMarkers(None)
        self.assertEqual(None, pm.process(
            Node("This has no paragraph", label=["a"])
        ))
        self.assertEqual(None, pm.process(
            Node("(b) Different paragraph", label=["a"])
        ))
        self.assertEqual(None, pm.process(
            Node("Later (a)", label=["a"])
        ))
        self.assertEqual(None, pm.process(
            Node("(a) Interpretation", label=["a", 'Interp'])
        ))

    def test_process_with_results(self):
        pm = ParagraphMarkers(None)
        self.assertEqual(pm.process(Node("(c) Paragraph", label=['c'])), [{
                "text": "(c)", "locations": [0]
        }])
        self.assertEqual(
            pm.process(Node("\n(vi) Paragraph", label=['c', 'vi'])), [{
                "text": "(vi)", "locations": [0]
            }]
        )
        self.assertEqual(
            pm.process(Node("ii. Paragraph", label=['ii', 'Interp'])), [{
                "text": "ii.", "locations": [0]
            }]
        )
        self.assertEqual(
            pm.process(Node("A. Paragraph", label=['ii', 'A', 'Interp'])),
            [{ "text": "A.", "locations": [0] }]
        )

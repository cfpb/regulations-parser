from reg_parser.layer.paragraph_markers import ParagraphMarkers
from reg_parser.tree import struct
from unittest import TestCase

class ParagraphMarkersTest(TestCase):

    def test_process_no_results(self):
        pm = ParagraphMarkers(None)
        self.assertEqual(None, pm.process(struct.node(
            "This has no paragraph", label=struct.label("a", ["a"])
        )))
        self.assertEqual(None, pm.process(struct.node(
            "(b) Different paragraph", label=struct.label("a", ["a"])
        )))
        self.assertEqual(None, pm.process(struct.node(
            "Later (a)", label=struct.label("a", ["a"])
        )))
        self.assertEqual(None, pm.process(struct.node("(a) Interpretation", 
            label=struct.label("Interpretations-a", ["Interpretations", "a"])
        )))

    def test_process_with_results(self):
        pm = ParagraphMarkers(None)
        self.assertEqual(pm.process(struct.node("(c) Paragraph",
            label=struct.label("c", ["c"]))), [{
                "text": "(c)", "locations": [0]
            }]
        )
        self.assertEqual(pm.process(struct.node("\n(vi) Paragraph",
            label=struct.label("c-vi", ["c", "vi"]))), [{
                "text": "(vi)", "locations": [0]
            }]
        )
        self.assertEqual(pm.process(struct.node("ii. Paragraph",
            label=struct.label("Interpretations-ii", 
                ["Interpretations", "ii"]))), [{
                "text": "ii.", "locations": [0]
            }]
        )
        self.assertEqual(pm.process(struct.node("A. Paragraph",
            label=struct.label("Interpretations-ii-A", 
                ["Interpretations", "ii", "A"]))), [{
                "text": "A.", "locations": [0]
            }]
        )

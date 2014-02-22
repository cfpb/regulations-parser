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
            Node("(a) Interpretation", label=["a", Node.INTERP_MARK],
                 node_type=Node.INTERP)
        ))
        self.assertEqual(None, pm.process(Node("References (a)",
                                               label=["111", "A", "a"],
                                               node_type=Node.APPENDIX)))
        self.assertEqual(None, pm.process(Node("References a.",
                                               label=["111", "A", "a"],
                                               node_type=Node.APPENDIX)))

    def test_process_with_results(self):
        pm = ParagraphMarkers(None)
        self.assertEqual(pm.process(Node("(c) Paragraph", label=['c'])),
                         [{"text": "(c)", "locations": [0]}])
        self.assertEqual(
            pm.process(Node("\n(vi) Paragraph", label=['c', 'vi'])), [{
                "text": "(vi)", "locations": [0]
            }]
        )
        self.assertEqual(
            pm.process(Node("ii. Paragraph",
                            label=['ii', Node.INTERP_MARK],
                            node_type=Node.INTERP)),
            [{"text": "ii.", "locations": [0]}]
        )
        self.assertEqual(
            pm.process(Node("A. Paragraph",
                            label=['ii', 'A', Node.INTERP_MARK],
                            node_type=Node.INTERP)),
            [{"text": "A.", "locations": [0]}]
        )
        self.assertEqual(
            pm.process(Node("(a) Paragraph",
                            label=['111', 'A', 'a'],
                            node_type=Node.APPENDIX)),
            [{'text': '(a)', 'locations': [0]}])
        self.assertEqual(
            pm.process(Node("a. Paragraph",
                            label=['111', 'A', 'a'],
                            node_type=Node.APPENDIX)),
            [{'text': 'a.', 'locations': [0]}])

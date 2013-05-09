from parser.layer.section_by_section import SectionBySection
from parser.tree import struct
from unittest import TestCase

class LayerSectionBySectionTest(TestCase):

    def test_process(self):
        notice1 = {
            "document_number": "111-22",
            "cfr_part": "100",
            "section_by_section": [{
                "title": "",
                "label": "100-22-b-2",
                "paragraphs": ["AAA"],
                "children": []
            }, {
                "title": "",
                "label": "100-22-b",
                "paragraphs": ["BBB"],
                "children": []
            }]
        }
        notice2 = {
            "document_number": "111-23",
            "cfr_part": "100",
            "section_by_section": [{
                "title": "",
                "paragraphs": [],
                "children": [{
                    "title": "",
                    "label": "100-22-b-2",
                    "paragraphs": ["CCC"],
                    "children": []
                }]
            }]
        }
        def mknode(label):
            return struct.node("", [], struct.label(label))
        s = SectionBySection(None, [notice1, notice2])
        self.assertEqual(None, s.process(mknode("100-55")))
        self.assertEqual(s.process(mknode("100-22-b")), 
            [{"text": 'BBB', "reference": ('111-22', '100-22-b')}])
        self.assertEqual(s.process(mknode("100-22-b-2")), [
            {"text": 'AAA', "reference": ('111-22', '100-22-b-2')},
            {"text": 'CCC', "reference": ('111-23', '100-22-b-2')}
            ])

    def test_concat_one_level(self):
        s = SectionBySection(None, None)
        self.assertEqual("AAA\nBBB\nCCC", s.concat({
            "title": "",
            "paragraphs": ["AAA", "BBB", "CCC"],
            "children": []
        }))

    def test_concat_multiple_levels(self):
        s = SectionBySection(None, None)
        self.assertEqual("AAA\nBBB\n\nCCC\nDDD\n\nEEE", s.concat({
            "title": "",
            "paragraphs": ["AAA", "BBB"],
            "children": [{
                "title": "",
                "paragraphs": ["CCC", "DDD"],
                "children": []
            }, {
                "title": "",
                "paragraphs": ["EEE"],
                "children": []
            }]
        }))


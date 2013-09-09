from unittest import TestCase

from regparser.layer.section_by_section import SectionBySection
from regparser.tree.struct import Node


class LayerSectionBySectionTest(TestCase):

    def test_process(self):
        notice1 = {
            "document_number": "111-22",
            "cfr_part": "100",
            'publication_date': '2008-08-08',
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
            'publication_date': '2009-09-09',
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
        s = SectionBySection(None, [notice1, notice2])
        self.assertEqual(None, s.process(Node(label=['100', '55'])))
        self.assertEqual(s.process(Node(label=['100', '22', 'b'])),
                         [{"reference": ('111-22', '100-22-b')}])
        self.assertEqual(s.process(Node(label=['100', '22', 'b', '2'])), [
            {"reference": ('111-22', '100-22-b-2')},
            {"reference": ('111-23', '100-22-b-2')}
            ])

    def test_process_empty(self):
        notice = {
            "document_number": "111-22",
            "cfr_part": "100",
            'publication_date': '2008-08-08',
            "section_by_section": [{
                "title": "",
                "label": "100-22-a",
                "paragraphs": [],
                "children": []
            }, {
                "title": "",
                "label": "100-22-b",
                "paragraphs": ["BBB"],
                "children": []
            }, {
                "title": "",
                "label": "100-22-c",
                "paragraphs": [],
                "children": [{
                    "label": "100-22-c-1",
                    "title": "",
                    "paragraphs": ["123"],
                    "children": []
                }]
            }, {
                "title": "",
                "label": "100-22-d",
                "paragraphs": [],
                "children": [{
                    "title": "",
                    "paragraphs": ["234"],
                    "children": []
                }]
            }]
        }
        s = SectionBySection(None, [notice])
        self.assertEqual(None, s.process(Node(label=['100-22-b-2'])))
        self.assertEqual(None, s.process(Node(label=['100-22-c'])))

    def test_process_order(self):
        notice1 = {
            "document_number": "111-22",
            "cfr_part": "100",
            "publication_date": "2010-10-10",
            "section_by_section": [{
                "title": "",
                "label": "100-22-b-2",
                "paragraphs": ["AAA"],
                "children": []
            }]
        }
        notice2 = {
            "document_number": "111-23",
            "cfr_part": "100",
            "publication_date": "2009-09-09",
            "section_by_section": [{
                "title": "",
                "label": "100-22-b-2",
                "paragraphs": ["CCC"],
                "children": []
            }]
        }
        s = SectionBySection(None, [notice1, notice2])
        self.assertEqual(s.process(Node(label=['100', '22', 'b', '2'])), [
            {"reference": ('111-23', '100-22-b-2')},
            {"reference": ('111-22', '100-22-b-2')}
            ])

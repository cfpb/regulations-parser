from unittest import TestCase

from regparser.layer.section_by_section import SectionBySection
from regparser.tree.struct import Node


class LayerSectionBySectionTest(TestCase):

    def test_process(self):
        notice1 = {
            "document_number": "111-22",
            "fr_volume": 22,
            "cfr_part": "100",
            'publication_date': '2008-08-08',
            "section_by_section": [{
                "title": "",
                "labels": ["100-22-b-2"],
                "paragraphs": ["AAA"],
                "page": 7677,
                "children": []
            }, {
                "title": "",
                "labels": ["100-22-b"],
                "paragraphs": ["BBB"],
                "page": 7676,
                "children": []
            }]
        }
        notice2 = {
            "document_number": "111-23",
            "fr_volume": 23,
            "cfr_part": "100",
            'publication_date': '2009-09-09',
            "section_by_section": [{
                "title": "",
                "paragraphs": [],
                "children": [{
                    "title": "",
                    "labels": ["100-22-b-2"],
                    "paragraphs": ["CCC"],
                    "page": 5454,
                    "children": []
                }]
            }]
        }
        s = SectionBySection(None, notices=[notice1, notice2])
        self.assertEqual(None, s.process(Node(label=['100', '55'])))
        self.assertEqual(s.process(Node(label=['100', '22', 'b'])),
                         [{"reference": ('111-22', '100-22-b'),
                           "publication_date": "2008-08-08",
                           "fr_volume": 22,
                           "fr_page": 7676}])
        self.assertEqual(s.process(Node(label=['100', '22', 'b', '2'])), [
            {"reference": ('111-22', '100-22-b-2'),
             "publication_date": "2008-08-08",
             "fr_volume": 22,
             "fr_page": 7677},
            {"reference": ('111-23', '100-22-b-2'),
             "publication_date": "2009-09-09",
             "fr_volume": 23,
             "fr_page": 5454}])

    def test_process_empty(self):
        notice = {
            "document_number": "111-22",
            "fr_volume": 22,
            "cfr_part": "100",
            'publication_date': '2008-08-08',
            "section_by_section": [{
                "title": "",
                "labels": ["100-22-a"],
                "paragraphs": [],
                "page": 7676,
                "children": []
            }, {
                "title": "",
                "label": "100-22-b",
                "paragraphs": ["BBB"],
                "page": 7677,
                "children": []
            }, {
                "title": "",
                "label": "100-22-c",
                "paragraphs": [],
                "page": 7678,
                "children": [{
                    "label": "100-22-c-1",
                    "title": "",
                    "paragraphs": ["123"],
                    "page": 7679,
                    "children": []
                }]
            }, {
                "title": "",
                "label": "100-22-d",
                "paragraphs": [],
                "page": 7680,
                "children": [{
                    "title": "",
                    "paragraphs": ["234"],
                    "page": 7681,
                    "children": []
                }]
            }]
        }
        s = SectionBySection(None, notices=[notice])
        self.assertEqual(None, s.process(Node(label=['100-22-b-2'])))
        self.assertEqual(None, s.process(Node(label=['100-22-c'])))

    def test_process_order(self):
        notice1 = {
            "document_number": "111-22",
            "fr_volume": 22,
            "cfr_part": "100",
            "publication_date": "2010-10-10",
            "section_by_section": [{
                "title": "",
                "labels": ["100-22-b-2"],
                "paragraphs": ["AAA"],
                "page": 7676,
                "children": []
            }]
        }
        notice2 = {
            "document_number": "111-23",
            "fr_volume": 23,
            "cfr_part": "100",
            "publication_date": "2009-09-09",
            "section_by_section": [{
                "title": "",
                "labels": ["100-22-b-2"],
                "paragraphs": ["CCC"],
                "page": 5454,
                "children": []
            }]
        }
        s = SectionBySection(None, notices=[notice1, notice2])
        self.assertEqual(s.process(Node(label=['100', '22', 'b', '2'])), [
            {"reference": ('111-23', '100-22-b-2'),
             "publication_date": "2009-09-09",
             "fr_volume": 23,
             "fr_page": 5454},
            {"reference": ('111-22', '100-22-b-2'),
             "publication_date": "2010-10-10",
             "fr_volume": 22,
             "fr_page": 7676}])

    def test_no_section_by_section(self):
        """Not all notices have a section-by-section analysis section. Verify
        that the parser doesn't explode in these cases"""
        notice = {
            "document_number": "111-22",
            "fr_volume": 22,
            "cfr_part": "100",
            "publication_date": "2010-10-10"
        }
        s = SectionBySection(None, notices=[notice])
        self.assertEqual(None, s.process(Node(label=['100', '22'])))

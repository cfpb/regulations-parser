# vim: set encoding=utf-8
from unittest import TestCase

from regparser.layer.meta import Meta
from regparser.tree.struct import Node
import settings


class LayerMetaTest(TestCase):

    def setUp(self):
        self.old_meta = settings.META
        settings.META = {}

    def tearDown(self):
        settings.META = self.old_meta

    def test_process_cfr(self):
        m = Meta(None, cfr_title=3)
        result = m.process(Node(label=['a']))
        self.assertEqual(1, len(result))
        self.assertTrue('cfr_title_number' in result[0])
        self.assertEqual(3, result[0]['cfr_title_number'])
        self.assertTrue('cfr_title_text' in result[0])
        self.assertEqual('The President', result[0]['cfr_title_text'])

    def test_process_effective_date(self):
        m = Meta(
            None,
            cfr_title=8,
            notices=[{'effective_on': '2001-01-01', 'document_number': 'v1'},
                     {'something': 'else', 'document_number': 'v2'},
                     {'effective_on': '2003-03-03',
                      'comments_close_on': '2004-04-04',
                      'document_number': 'v3'},
                     {'dates': {'other': ['2005-05-05']},
                      'document_number': 'v4'}],
            version='v3')
        result = m.process(Node(label=['a']))
        self.assertEqual(1, len(result))
        self.assertTrue('effective_date' in result[0])
        self.assertEqual('2003-03-03', result[0]['effective_date'])

        m = Meta(None, 9, [], None)
        result = m.process(Node(label=['a']))
        self.assertEqual(1, len(result))
        self.assertFalse('effective_date' in result[0])

    def test_process_chronological(self):
        m = Meta(None,
                 cfr_title=12,
                 notices=[{'effective_on': '2003-03-03',
                           'document_number': 'v1'},
                          {'effective_on': '2001-01-01',
                           'document_number': 'v2'}],
                 version='v1')
        result = m.process(Node(label=['a']))
        self.assertEqual('2003-03-03', result[0]['effective_date'])

    def test_process_extra(self):
        settings.META = {'some': 'setting', 'then': 42}
        m = Meta(None, cfr_title=19)
        result = m.process(Node(label=['a']))
        self.assertEqual(1, len(result))
        self.assertTrue('some' in result[0])
        self.assertEqual('setting', result[0]['some'])
        self.assertTrue('then' in result[0])
        self.assertEqual(42, result[0]['then'])

    def test_process_not_root(self):
        m = Meta(None, cfr_title=19)
        result = m.process(Node(label=['111', '22']))
        self.assertEqual(None, result)

    def test_process_statutory_letter(self):
        m = Meta(None, cfr_title=19)
        result = m.process(Node(label=['1111']))
        self.assertFalse('statutory_name' in result[0])
        self.assertFalse('reg_letter' in result[0])

        result = m.process(Node(label=['1111'],
                           title=u"PART 1111—RAGGEDY REG (REGULATION R)"))
        self.assertEqual('RAGGEDY REG', result[0]['statutory_name'])
        self.assertEqual('R', result[0]['reg_letter'])

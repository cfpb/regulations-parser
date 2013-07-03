from regparser.layer.meta import Meta
from regparser.tree import struct
import settings
from unittest import TestCase

class LayerMetaTest(TestCase):

    def setUp(self):
        self.old_meta = settings.META
        settings.META  = {}

    def tearDown(self):
        settings.META = self.old_meta

    def test_process_cfr(self):
        m = Meta(None, 3, [])
        result = m.process(struct.node('', [], struct.label('a', ['a'])))
        self.assertEqual(1, len(result))
        self.assertTrue('cfr_title_number' in result[0])
        self.assertEqual(3, result[0]['cfr_title_number'])
        self.assertTrue('cfr_title_text' in result[0])
        self.assertEqual('The President', result[0]['cfr_title_text'])

    def test_process_effective_date(self):
        m = Meta(None, 8, [
            {'dates': {'effective': ['2001-01-01']}},
            {'something': 'else'},
            {'dates': {
                'effective': ['2002-02-02', '2003-03-03'],
                'comment': ['2004-04-04']
            }},
            {'dates': {'other': ['2005-05-05']}}])
        result = m.process(struct.node('', [], struct.label('a', ['a'])))
        self.assertEqual(1, len(result))
        self.assertTrue('effective_date' in result[0])
        self.assertEqual('2003-03-03', result[0]['effective_date'])

        m = Meta(None, 9, [])
        result = m.process(struct.node('', [], struct.label('a', ['a'])))
        self.assertEqual(1, len(result))
        self.assertFalse('effective_date' in result[0])

    def test_process_extra(self):
        settings.META = {'some': 'setting', 'then': 42}
        m = Meta(None, 19, [])
        result = m.process(struct.node('', [], struct.label('a', ['a'])))
        self.assertEqual(1, len(result))
        self.assertTrue('some' in result[0])
        self.assertEqual('setting', result[0]['some'])
        self.assertTrue('then' in result[0])
        self.assertEqual(42, result[0]['then'])

    def test_process_not_root(self):
        m = Meta(None, 19, [])
        result = m.process(struct.node('', [], struct.label('111-22',
            ['111', '22'])))
        self.assertEqual(None, result)

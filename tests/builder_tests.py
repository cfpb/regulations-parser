from unittest import TestCase

from mock import patch

from regparser.builder import Builder


class BuilderTests(TestCase):
    @patch.object(Builder, 'merge_changes')
    @patch.object(Builder, '__init__')
    def test_revision_generator_notices(self, init, merge_changes):
        init.return_value = None
        merge_changes = []
        b = Builder()   # Don't need parameters as init's been mocked out
        aaaa = {'document_number': 'aaaa', 'effective_on': '2012-12-12',
                'publication_date': '2011-11-11', 'changes': []}
        bbbb = {'document_number': 'bbbb', 'effective_on': '2012-12-12',
                'publication_date': '2011-11-12', 'changes': []}
        cccc = {'document_number': 'cccc', 'effective_on': '2013-01-01',
                'publication_date': '2012-01-01', 'changes': []}
        b.notices = [aaaa, bbbb, cccc]
        b.eff_notices = {'2012-12-12': [aaaa, bbbb], '2013-01-01': [cccc]}
        b.doc_number = 'aaaa'
        tree = {}
        version_list = []
        notice_lists = []
        for version, _, _, notices in b.revision_generator(tree):
            version_list.append(version)
            notice_lists.append(notices)
        self.assertEqual(['bbbb', 'cccc'], version_list)
        self.assertEqual(2, len(notice_lists))

        self.assertEqual(2, len(notice_lists[0]))
        self.assertTrue(aaaa in notice_lists[0])
        self.assertTrue(bbbb in notice_lists[0])

        self.assertEqual(3, len(notice_lists[1]))
        self.assertTrue(aaaa in notice_lists[1])
        self.assertTrue(bbbb in notice_lists[1])
        self.assertTrue(cccc in notice_lists[1])

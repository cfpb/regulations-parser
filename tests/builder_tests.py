from unittest import TestCase

from mock import Mock, patch

from regparser.builder import Builder, LayerCacheAggregator
from regparser.tree.struct import Node


class BuilderTests(TestCase):
    @patch.object(Builder, 'merge_changes')
    @patch.object(Builder, '__init__')
    def test_revision_generator_notices(self, init, merge_changes):
        init.return_value = None
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
        tree = Node(label=['1111'])
        version_list = []
        notice_lists = []
        for notice, _, _, notices in b.revision_generator(tree):
            version_list.append(notice['document_number'])
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

    @patch.object(Builder, '__init__')
    def test_layer_cache(self, init):
        """Integration test for layer caching"""
        init.return_value = None
        cache = LayerCacheAggregator()
        b = Builder()   # Don't need parameters as init's been mocked out
        b.cfr_title, b.cfr_part, b.doc_number = 15, '111', '111-222'
        b.writer = Mock()
        write = b.writer.layer.return_value.write
        tree = Node(label=["1234"], children=[
            Node(label=["1234", "1"], children=[
                Node("See paragraph (b)", label=["1234", "1", "a"]),
                Node("This is b", label=["1234", "1", "b"])])])
        b.gen_and_write_layers(tree, [], cache, [])
        arg = write.call_args_list[3][0][0]
        self.assertEqual(['1234-1-a'], arg.keys())
        cache.replace_using(tree)

        write.reset_mock()
        tree.children[0].children[1].text = "References paragraph (a)"
        b.gen_and_write_layers(tree, [], cache, [])
        arg = write.call_args_list[3][0][0]
        self.assertEqual(['1234-1-a'], arg.keys())

        write.reset_mock()
        tree.children[0].children[0].text = "Contains no references"
        b.gen_and_write_layers(tree, [], cache, [])
        arg = write.call_args_list[3][0][0]
        self.assertEqual(['1234-1-a'], arg.keys())

        write.reset_mock()
        notice = {}
        cache.invalidate_by_notice(notice)
        b.gen_and_write_layers(tree, [], cache, [])
        arg = write.call_args_list[3][0][0]
        self.assertEqual(['1234-1-a'], arg.keys())

        write.reset_mock()
        notice['changes'] = {'1234-1-b': 'some change'}
        cache.invalidate_by_notice(notice)
        b.gen_and_write_layers(tree, [], cache, [])
        arg = write.call_args_list[3][0][0]
        self.assertEqual(['1234-1-a', '1234-1-b'], list(sorted(arg.keys())))

        write.reset_mock()
        notice['changes'] = {'1234-Subpart-A': 'some change'}
        cache.invalidate_by_notice(notice)
        b.gen_and_write_layers(tree, [], cache, [])
        arg = write.call_args_list[3][0][0]
        self.assertEqual(['1234-1-b'], list(sorted(arg.keys())))


class LayerCacheAggregatorTests(TestCase):
    def test_invalidate(self):
        cache = LayerCacheAggregator()
        cache._known_labels = set(['123', '123-1', '123-1-a',
                                   '123-1-a-Interp'])
        cache.invalidate(['123-2'])
        self.assertEqual(cache._known_labels,
                         set(['123', '123-1', '123-1-a', '123-1-a-Interp']))

        cache.invalidate(['123-2', '123-1-Interp'])
        self.assertEqual(cache._known_labels, set(['123']))

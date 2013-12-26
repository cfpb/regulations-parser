from unittest import TestCase

from mock import patch

from regparser import content
import settings


class ContentTests(TestCase):
    def test_try_to_load(self):
        self.assertEqual(None, content._try_to_load('aaa.bbb.ccc'))
        self.assertEqual(None, content._try_to_load('tests.foo.baz'))
        self.assertEqual({'content': 'here'},
                         content._try_to_load('tests.foo.bar'))


class MacrosTests(TestCase):
    def setUp(self):
        self._original_macros = getattr(settings, 'MACROS_SOURCES', None)

    def tearDown(self):
        if (self._original_macros is None
                and hasattr(settings, 'MACROS_SOURCES')):
            del settings.MACROS_SOURCES
        else:
            settings.MACROS_SOURCES = self._original_macros

    @patch('regparser.content._try_to_load')
    def test_iterate(self, try_to_load):
        def response(path):
            if path == 'return_none':
                return None
            else:
                return [('a', 'b'), ('c', 'd')]
        try_to_load.side_effect = response

        settings.MACROS_SOURCES = ['source1', 'return_none', 'source2']

        pairs = [pair for pair in content.Macros()]
        self.assertEqual(pairs, [('a', 'b'), ('c', 'd'),    # source1
                                 ('a', 'b'), ('c', 'd')])   # source2

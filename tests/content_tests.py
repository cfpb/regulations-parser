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
        def response(path, _):
            if path == 'return_none':
                return None
            else:
                return [('a', 'b'), ('c', 'd')]
        try_to_load.side_effect = response

        settings.MACROS_SOURCES = ['source1', 'return_none', 'source2']

        pairs = [pair for pair in content.Macros()]
        self.assertEqual(pairs, [('a', 'b'), ('c', 'd'),    # source1
                                 ('a', 'b'), ('c', 'd')])   # source2


class GetterBase(object):
    """Shared base class for 'getter' content. See below for examples.
    Cannot derive from TestCase, lest the test runner execute it"""
    settings_key = None

    def setUp(self):
        self._original = getattr(settings, self.settings_key, None)

    def content_obj(self):
        """Overridden in children"""
        raise NotImplemented

    def tearDown(self):
        if (self._original is None
                and hasattr(settings, self.settings_key)):
            delattr(settings, self.settings_key)
        else:
            setattr(settings, self.settings_key, self._original)

    @patch('regparser.content._try_to_load')
    def test_get(self, try_to_load):
        def response(path, _):
            if path == 'source1':
                return {'source': 1}
            if path == 'return_none':
                return None
            else:
                return {'a': 'b', 'source': 2}
        try_to_load.side_effect = response

        setattr(settings, self.settings_key,
                ['source1', 'return_none', 'source2'])

        overrides = self.content_obj()
        self.assertEqual(1, overrides.get('source'))
        self.assertEqual('b', overrides.get('a'))
        self.assertEqual(None, overrides.get('other'))
        self.assertEqual('foo', overrides.get('other', 'foo'))


class ImageOverridesTests(GetterBase, TestCase):
    settings_key = 'OVERRIDES_SOURCES'

    def content_obj(self):
        return content.ImageOverrides()


class RegPatchesTests(GetterBase, TestCase):
    settings_key = 'REGPATCHES_SOURCES'

    def content_obj(self):
        return content.RegPatches()

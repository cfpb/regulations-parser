from unittest import TestCase

from reg_parser.layer.graphics import Graphics
from reg_parser.tree import struct
import settings

class LayerGraphicsTest(TestCase):

    def setUp(self):
        self.overrides = settings.IMAGE_OVERRIDES
        self.default_url = settings.DEFAULT_IMAGE_URL

    def tearDown(self):
        settings.IMAGE_OVERRIDES = self.overrides
        settings.DEFAULT_IMAGE_URL = self.default_url

    def test_process(self):
        node = struct.node("Testing ![ex](ABCD) then some more XXX " +
            "some more ![222](XXX) followed by ![ex](ABCD) and XXX")
        g = Graphics(None)
        result = g.process(node)
        self.assertEqual(2, len(result))
        found = [False, False]
        for res in result:
            if (res['text'] == '![ex](ABCD)'
                and 'ABCD' in res['url']
                and res['alt'] == 'ex'
                and res['locations'] == [0, 1]):
                found[0] = True
            elif (res['text'] == '![222](XXX)'
                and 'XXX' in res['url']
                and res['alt'] == '222'
                and res['locations'] == [0]):
                found[1] = True
        self.assertEqual([True, True], found)

    def test_process_format(self):
        node = struct.node("![A88 Something](ER22MY13.257)")
        g = Graphics(None)
        self.assertEqual(1, len(g.process(node)))

    def test_process_custom_url(self):
        settings.DEFAULT_IMAGE_URL = ":::::%s:::::"
        settings.IMAGE_OVERRIDES = {"a": "AAA", "f": "F8"}

        node = struct.node("![Alt1](img1)   ![Alt2](f)  ![Alt3](a)")
        g = Graphics(None)
        results = g.process(node)
        self.assertEqual(3, len(results))
        found = [False, False, False]
        for result in results:
            if result['alt'] == 'Alt1' and result['url'] == ':::::img1:::::':
                found[0] = True
            elif result['alt'] == 'Alt2' and result['url'] == 'F8':
                found[1] = True
            elif result['alt'] == 'Alt3' and result['url'] == 'AAA':
                found[2] = True
        self.assertEqual([True, True, True], found)

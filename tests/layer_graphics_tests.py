from parser.layer.graphics import Graphics
from parser.tree import struct
from unittest import TestCase

class LayerGraphicsTest(TestCase):

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

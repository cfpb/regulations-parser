from parser.layer.graphics import Graphics
from parser.tree import struct
from unittest import TestCase

class LayerGraphicsTest(TestCase):

    def test_process(self):
        node = struct.node("Testing <GID>ABCD</GID> then some more XXX " +
            "some more <GID>XXX</GID> followed by <GID>ABCD</GID> and XXX")
        g = Graphics(None)
        result = g.process(node)
        self.assertEqual(2, len(result))
        found = [False, False]
        for res in result:
            if (res['text'] == '<GID>ABCD</GID>'
                and 'ABCD' in res['url']
                and res['locations'] == [0, 1]):
                found[0] = True
            elif (res['text'] == '<GID>XXX</GID>'
                and 'XXX' in res['url']
                and res['locations'] == [0]):
                found[1] = True
        self.assertEqual([True, True], found)

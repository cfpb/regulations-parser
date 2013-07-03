from unittest import TestCase

from regparser.layer.layer import *
from regparser.tree import struct

class ExampleLayer(Layer):
    pass

class LayerLayerTest(TestCase):
    """Test default implementations"""

    def test_pre_process(self):
        el = ExampleLayer(struct.node('some text'))
        self.assertEqual(None, el.pre_process())
    
    def test_process(self):
        el = ExampleLayer(struct.node("other text"))
        self.assertEqual(NotImplemented, el.process(struct.node("oo")))

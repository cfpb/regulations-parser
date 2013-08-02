from unittest import TestCase

from regparser.layer.layer import *
from regparser.tree.struct import Node

class ExampleLayer(Layer):
    pass

class LayerLayerTest(TestCase):
    """Test default implementations"""

    def test_pre_process(self):
        el = ExampleLayer(Node('some text'))
        self.assertEqual(None, el.pre_process())
    
    def test_process(self):
        el = ExampleLayer(Node("other text"))
        self.assertEqual(NotImplemented, el.process(Node("oo")))

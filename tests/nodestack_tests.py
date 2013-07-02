#vim: set encoding=utf-8
from unittest import TestCase
from reg_parser.tree.node_stack import NodeStack

class NodeStackTest(TestCase):
    def test_size(self):
        nstack = NodeStack()
        self.assertEquals(nstack.size(), 1)

        nstack.push('A')
        nstack.push('B')

        nstack.push_last('C')

        self.assertEquals(nstack.size(), 3)

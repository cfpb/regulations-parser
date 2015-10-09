# vim: set encoding=utf-8
from unittest import TestCase

from regparser.tree.priority_stack import PriorityStack


class PriorityStackTest(TestCase):
    def test_size(self):
        nstack = PriorityStack()
        self.assertEquals(nstack.size(), 1)

        nstack.push('A')
        nstack.push('B')

        nstack.push_last('C')

        self.assertEquals(nstack.size(), 3)

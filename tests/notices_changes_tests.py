#vim: set encoding=utf-8
from unittest import TestCase
from regparser.notice import changes
from regparser.tree.struct import Node


class ChangesTests(TestCase):
    def test_find_candidate(self):
        n1 = Node('n1', label=['200', '1'])
        n2 = Node('n1i', label=['200', 1, 'i'])
        n3 = Node('n2', label=['200', '2'])
        n4 = Node('n3', label=['200', '3'])
        n5 = Node('n3a', label=['200', '3', 'a'])

        n1.children = [n2]
        n4.children = [n5]
        root = Node('root', label=['200'], children=[n1, n3, n4])

        result = changes.find_candidate(root, 'i')[0]
        self.assertEqual(u'n1i', result.text)

    def test_not_find_candidate(self):
        n1 = Node('n1', label=['200', '1'])
        n2 = Node('n1i', label=['200', 1, 'i'])
        n3 = Node('n2', label=['200', '2'])
        n4 = Node('n3', label=['200', '3'])
        n5 = Node('n3a', label=['200', '3', 'a'])

        n1.children = [n2]
        n4.children = [n5]
        root = Node('root', label=['200'], children=[n1, n3, n4])

        result = changes.find_candidate(root, 'j')
        self.assertEqual(result, [])

    def test_fix_label(self):
        self.assertEqual(
            ['200', '1', 'a'], 
            changes.fix_label('200-?-1-a'))

        self.assertEqual(
            ['200', '1', 'a', 'ii'],
            changes.fix_label('200-1-a-ii'))

        self.assertEqual(
            ['200'], 
            changes.fix_label('200'))

        self.assertEqual(
            ['200', '1', 'a'],
            changes.fix_label('200-1-a[text]'))

    def test_fix_labels(self):
        amended = [
            ('POST', '205-?-1-a'), 
            ('PUT', '205-?-1-b[text]'), 
            ('MOVE', ('205-?-2-a', '205-?-2-j'))]
        fixed = changes.fix_labels(amended)
        post = fixed[0]
        put = fixed[1]
        move = fixed[2]

        self.assertEqual(post[1], ['205', '1', 'a'])
        self.assertEqual(post[2], '205-1-a')

        self.assertEqual(put[1], ['205', '1', 'b'])
        self.assertEqual(put[2], '205-1-b')

        self.assertEqual(move[1], [['205', '2', 'a'], ['205', '2', 'j']])
        self.assertEqual(move[2], ['205-2-a', '205-2-j'])

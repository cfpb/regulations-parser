# vim: set fileencoding=utf-8
from unittest import TestCase

from regparser.layer.key_terms import KeyTerms
from regparser.tree.struct import Node


class LayerKeyTermTest(TestCase):

    def test_find_keyterm(self):
        node = Node(
            '(a) Apples. Apples are grown in New Zealand.',
            label=['101', '22', 'a'])
        node.tagged_text = '(a) <E T="03">Apples.</E> Apples are grown in '
        node.tagged_text += 'New Zealand.'
        kt = KeyTerms(None)
        results = kt.process(node)
        self.assertNotEqual(results, None)
        self.assertEqual(results[0]['key_term'], 'Apples.')
        self.assertEqual(results[0]['locations'], [0])

    def test_keyterm_definition(self):
        node = Node("(a) Terminator means I'll be back",
                    label=['101', '22', 'a'])
        node.tagged_text = """(a) <E T="03">Terminator</E> means I'll be """
        node.tagged_text += 'back'
        kt = KeyTerms(None)
        results = kt.process(node)
        self.assertEqual(results, None)

        node = Node("(1) Act means pretend", label=['101', '22', 'a', '1'])
        node.tagged_text = """(1) <E T="03">Act</E> means pretend"""
        node = Node(
            "(1) Act means the Truth in Lending Act (15 U.S.C. 1601 et seq.).",
            label=['1026', '2', 'a', '1'])
        node.tagged_text = (
            '(1) <E T="03">Act</E> means the Truth in Lending Act (15 U.S.C. '
            '1601 <E T="03">et seq.</E>).')
        kt = KeyTerms(None)
        results = kt.process(node)
        self.assertEqual(results, None)

    def test_emphasis_later(self):
        """ Don't pick up something that is emphasized later in a paragraph as
        a key-term. """

        node = Node('(a) This has a list: apples et seq.',
                    label=['101', '22', 'a'])
        node.tagged_text = '(a) This has a list: apples <E T="03">et seq.</E>'

        kt = KeyTerms(None)
        results = kt.process(node)
        self.assertEqual(results, None)

    def test_keyterm_is_first_not_first(self):
        node = Node('(a) This has a list: apples et seq.',
                    label=['101', '22', 'a'])
        node.tagged_text = '(a) This has a list: apples <E T="03">et seq.</E>'

        kt = KeyTerms(None)
        self.assertFalse(kt.keyterm_is_first(node, 'et seq.'))

    def test_emphasis_close_to_front(self):
        """ An emphasized word is close to the front, but is not a key term.
        """

        node = Node('(a) T et seq. has a list: apples',
                    label=['101', '22', 'a'])
        node.tagged_text = '(a) T <E T="03">et seq.</E> has a list: apples'

        kt = KeyTerms(None)
        self.assertFalse(kt.keyterm_is_first(node, 'et seq.'))

    def test_interpretation_markers(self):
        node = Node('3. et seq. has a list: apples',
                    label=['101', 'c', Node.INTERP_MARK, '3'],
                    node_type=Node.INTERP)
        node.tagged_text = '3. <E T="03">et seq.</E> has a list: apples'
        kt = KeyTerms(None)
        results = kt.process(node)
        self.assertNotEqual(results, None)
        self.assertEqual(results[0]['key_term'], 'et seq.')
        self.assertEqual(results[0]['locations'], [0])

    def test_no_keyterm(self):
        node = Node('(a) Apples are grown in New Zealand.',
                    label=['101', '22', 'a'])
        node.tagged_text = '(a) Apples are grown in New Zealand.'
        kt = KeyTerms(None)
        results = kt.process(node)
        self.assertEquals(results, None)

    def test_keyterm_and_emphasis(self):
        node = Node('(a) Apples. Apples are grown in '
                    + 'New Zealand.', label=['101', '22', 'a'])
        node.tagged_text = '(a) <E T="03">Apples.</E> Apples are grown in ' +\
            'New <E T="03">Zealand.</E>'
        kt = KeyTerms(None)
        results = kt.process(node)
        self.assertNotEqual(results, None)
        self.assertEqual(results[0]['key_term'], 'Apples.')
        self.assertEqual(results[0]['locations'], [0])

    def test_keyterm_see_also(self):
        """ Keyterm tags sometimes enclose phrases such as 'See also' because
        those tags are also used for emphasis. """

        node = Node('(a) Apples. See also Section 101.2',
                    label=['101', '22', 'a'])
        node.tagged_text = '(a) <E T="03">Apples. See also</E>'

        kt = KeyTerms(None)
        results = kt.process(node)
        self.assertEqual('Apples.', results[0]['key_term'])

    def test_keyterm_see(self):
        """ Keyterm tags sometimes enclose phrases such as 'See also' because
        those tags are also used for emphasis. """

        node = Node('(a) Apples. See Section 101.2',
                    label=['101', '22', 'a'])
        node.tagged_text = '(a) <E T="03">Apples. See also</E>'

        kt = KeyTerms(None)
        results = kt.process(node)
        self.assertEqual('Apples.', results[0]['key_term'])

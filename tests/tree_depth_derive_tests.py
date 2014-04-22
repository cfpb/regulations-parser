from unittest import TestCase

from regparser.tree.depth.derive import derive_depths


class DeriveTests(TestCase):
    def test_ints(self):
        results = derive_depths(['1', '2', '3', '4'])
        self.assertEqual(1, len(results))
        self.assertEqual([0, 0, 0, 0], [r[1] for r in results[0]])

    def test_alpha_ints(self):
        results = derive_depths(['A', '1', '2', '3'])
        self.assertEqual(1, len(results))
        self.assertEqual([0, 1, 1, 1], [r[1] for r in results[0]])

    def test_alpha_ints_jump_back(self):
        results = derive_depths(['A', '1', '2', '3', 'B', '1', '2', '3', 'C'])
        self.assertEqual(1, len(results))
        self.assertEqual([0, 1, 1, 1, 0, 1, 1, 1, 0],
                         [r[1] for r in results[0]])

    def test_roman_alpha(self):
        results = derive_depths(['a', '1', '2', 'b', '1', '2', '3', '4', 'i',
                                 'ii', 'iii', '5', 'c', 'd', '1', '2', 'e'])
        self.assertEqual(1, len(results))
        self.assertEqual([0, 1, 1, 0, 1, 1, 1, 1, 2, 2, 2, 1, 0, 0, 1, 1, 0],
                         [r[1] for r in results[0]])

    def test_mix_levels_roman_alpha(self):
        results = derive_depths(['A', '1', '2', 'i', 'ii', 'iii', 'iv', 'B',
                                 '1', 'a', 'b', '2', 'a', 'b', 'i', 'ii',
                                 'iii', 'c'])
        self.assertEqual(1, len(results))
        self.assertEqual([0, 1, 1, 2, 2, 2, 2, 0, 1, 2, 2, 1, 2, 2, 3, 3, 3,
                          2], [r[1] for r in results[0]])

    def test_i_ambiguity(self):
        results = derive_depths(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'])
        self.assertEqual(2, len(results))
        results = [[r[1] for r in result] for result in results]
        self.assertTrue([0, 0, 0, 0, 0, 0, 0, 0, 0] in results)
        self.assertTrue([0, 0, 0, 0, 0, 0, 0, 0, 1] in results)

        results = derive_depths(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i',
                                 'j'])
        self.assertEqual(1, len(results))
        self.assertEqual([0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                         [r[1] for r in results[0]])

        results = derive_depths(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i',
                                 'ii'])
        self.assertEqual(1, len(results))
        self.assertEqual([0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
                         [r[1] for r in results[0]])

    def test_repeat_alpha(self):
        results = derive_depths(['A', '1', 'a', 'i', 'ii', 'a', 'b', 'c', 'b'])
        self.assertEqual(1, len(results))
        self.assertEqual([0, 1, 2, 3, 3, 4, 4, 4, 2],
                         [r[1] for r in results[0]])

    def test_simple_stars(self):
        results = derive_depths(['A', '1', '*', 'd'])
        self.assertEqual(1, len(results))
        self.assertEqual([0, 1, 2, 2], [r[1] for r in results[0]])

        results = derive_depths(['A', '1', 'a', '*', 'd'])
        self.assertEqual(1, len(results))
        self.assertEqual([0, 1, 2, 2, 2], [r[1] for r in results[0]])

    def test_ambiguous_stars(self):
        results = derive_depths(['A', '1', 'a', '*', 'B'])
        self.assertEqual(4, len(results))
        results = [[r[1] for r in result] for result in results]
        self.assertTrue([0, 1, 2, 3, 3] in results)
        self.assertTrue([0, 1, 2, 3, 0] in results)
        self.assertTrue([0, 1, 2, 2, 0] in results)
        self.assertTrue([0, 1, 2, 1, 0] in results)

    def test_double_stars(self):
        results = derive_depths(['A', '1', 'a', '*', '*', 'B'])
        self.assertEqual(3, len(results))
        results = [[r[1] for r in result] for result in results]
        self.assertTrue([0, 1, 2, 2, 1, 0] in results)
        self.assertTrue([0, 1, 2, 3, 2, 0] in results)
        self.assertTrue([0, 1, 2, 3, 1, 0] in results)

    def test_start_star(self):
        results = derive_depths(['i', 'ii', '*', 'v', '*', 'vii'])
        self.assertEqual(3, len(results))
        results = [[r[1] for r in result] for result in results]
        self.assertTrue([0, 0, 1, 1, 2, 2] in results)
        self.assertTrue([0, 0, 1, 1, 0, 0] in results)
        self.assertTrue([0, 0, 0, 0, 0, 0] in results)
        results = derive_depths(['*', 'c', '1', '*', 'ii', 'iii', '2', 'i',
                                 'ii', '*', 'v', '*', 'vii', 'A'])
        self.assertEqual(3, len(results))
        results = [[r[1] for r in result] for result in results]
        self.assertTrue([0, 0, 1, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 3] in results)
        self.assertTrue([0, 0, 1, 2, 2, 2, 1, 2, 2, 3, 3, 2, 2, 3] in results)
        self.assertTrue([0, 0, 1, 2, 2, 2, 1, 2, 2, 3, 3, 4, 4, 5] in results)

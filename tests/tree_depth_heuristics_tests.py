from unittest import TestCase

from regparser.tree.depth import markers
from regparser.tree.depth.derive import Solution
from regparser.tree.depth.heuristics import prefer_multiple_children


class HeuristicsTests(TestCase):
    def test_prefer_multiple_children(self):
        solution1 = {'type0': markers.lower, 'idx0': 0, 'depth0': 0,    # a
                     'type1': markers.lower, 'idx1': 1, 'depth1': 0,    # b
                     'type2': markers.lower, 'idx2': 2, 'depth2': 0,
                     'type3': markers.lower, 'idx3': 3, 'depth3': 0,
                     'type4': markers.lower, 'idx4': 4, 'depth4': 0,
                     'type5': markers.lower, 'idx5': 5, 'depth5': 0,
                     'type6': markers.lower, 'idx6': 6, 'depth6': 0,
                     'type7': markers.lower, 'idx7': 7, 'depth7': 0,    # h
                     'type8': markers.lower, 'idx8': 8, 'depth8': 0}    # i
        solution2 = solution1.copy()
        solution2['type8'] = markers.roman
        solution2['idx8'] = 0
        solution2['depth8'] = 1

        solutions = [Solution(solution1), Solution(solution2)]
        solutions = prefer_multiple_children(solutions, 0.5)
        self.assertEqual(solutions[0].weight, 1.0)
        self.assertTrue(solutions[1].weight < solutions[0].weight)

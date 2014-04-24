from constraint import Problem

from regparser.tree.depth import markers, rules


def solPrint(solutions):
    print "Num solutions:", len(solutions)
    for solution in solutions:
        for idx in range(len(solution)/3):
            index = solution["idx" + str(idx)]
            marker = solution["type" + str(idx)][index]
            depth = solution["depth" + str(idx)]
            print " "*4*depth + marker
        print "------------"


class ParAssignment(object):
    def __init__(self, typ, idx, depth):
        self.typ = typ
        self.idx = idx
        self.depth = depth


class Solution(object):
    def __init__(self, assignment, weight=1.0):
        self.weight = weight
        self.assignment = []
        for i in range(len(assignment) / 3):
            self.assignment.append(
                ParAssignment(assignment['type' + str(i)],
                              assignment['idx' + str(i)],
                              assignment['depth' + str(i)]))

    def cp_with_penalty(self, penalty):
        sol = Solution([], self.weight * (1 - penalty))
        sol.assignment = self.assignment
        return sol

    def __iter__(self):
        return iter(self.assignment)


def derive_depths(marker_chars, additional_constraints=[]):
    if not marker_chars:
        return []
    problem = Problem()
    constrain = problem.addConstraint       # shorthand

    # Marker type per marker
    problem.addVariables(["type" + str(i) for i in range(len(marker_chars))],
                         markers.types)
    # Index within the marker list
    problem.addVariables(["idx" + str(i) for i in range(len(marker_chars))],
                         range(51))
    # Depth in the tree, with an arbitrary limit of 10
    problem.addVariables(["depth" + str(i) for i in range(len(marker_chars))],
                         range(10))
    all_vars = []
    for i in range(len(marker_chars)):
        all_vars.extend(['type' + str(i), 'idx' + str(i), 'depth' + str(i)])

    # Always start at depth 0
    constrain(rules.must_be(0), ("depth0",))

    for idx, marker in enumerate(marker_chars):
        idx_str = str(idx)
        constrain(rules.type_match(marker),
                  ("type" + idx_str, "idx" + idx_str))

        prior_params = ['type' + idx_str, 'idx' + idx_str, 'depth' + idx_str]
        for i in range(idx):
            prior_params += ['type' + str(i), 'idx' + str(i), 'depth' + str(i)]

        constrain(rules.same_type, prior_params)
        constrain(rules.diff_type, prior_params)

    constrain(rules.same_depth_same_type, all_vars)
    constrain(rules.stars_occupy_space, all_vars)

    for constraint in additional_constraints:
        constraint(constrain, all_vars)

    solPrint(problem.getSolutions())
    return [Solution(solution) for solution in problem.getSolutions()]

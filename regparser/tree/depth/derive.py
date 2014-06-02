from constraint import Problem

from regparser.tree.depth import markers, rules


class ParAssignment(object):
    """A paragraph's type, index, depth assignment"""
    def __init__(self, typ, idx, depth):
        self.typ = typ
        self.idx = idx
        self.depth = depth


class Solution(object):
    """A collection of assignments + a weight for how likely this solution is
    (after applying heuristics)"""
    def __init__(self, assignment, weight=1.0):
        self.weight = weight
        self.assignment = []
        if isinstance(assignment, list):
            self.assignment = assignment
        else:   # assignment is a dict (as returned by constraint solver)
            for i in range(len(assignment) / 3):    # for (type, idx, depth)
                self.assignment.append(
                    ParAssignment(assignment['type' + str(i)],
                                  assignment['idx' + str(i)],
                                  assignment['depth' + str(i)]))

    def copy_with_penalty(self, penalty):
        """Immutable copy while modifying weight"""
        sol = Solution([], self.weight * (1 - penalty))
        sol.assignment = self.assignment
        return sol

    def __iter__(self):
        return iter(self.assignment)

    def pretty_print(self):
        for par in self.assignment:
            print " "*4*par.depth + par.typ[par.idx]


def derive_depths(marker_list, additional_constraints=[]):
    """Use constraint programming to derive the paragraph depths associated
    with a list of paragraph markers. Additional constraints (e.g. expected
    marker types, etc.) can also be added. Such constraints are functions of
    two parameters, the constraint function (problem.addConstraint) and a
    list of all variables"""
    if not marker_list:
        return []
    problem = Problem()

    # Marker type per marker
    problem.addVariables(["type" + str(i) for i in range(len(marker_list))],
                         markers.types)
    # Index within the marker list
    problem.addVariables(["idx" + str(i) for i in range(len(marker_list))],
                         range(51))
    # Depth in the tree, with an arbitrary limit of 10
    problem.addVariables(["depth" + str(i) for i in range(len(marker_list))],
                         range(10))
    all_vars = []
    for i in range(len(marker_list)):
        all_vars.extend(['type' + str(i), 'idx' + str(i), 'depth' + str(i)])

    # Always start at depth 0
    problem.addConstraint(rules.must_be(0), ("depth0",))

    for idx, marker in enumerate(marker_list):
        idx_str = str(idx)
        problem.addConstraint(rules.type_match(marker),
                              ("type" + idx_str, "idx" + idx_str))

        prior_params = ['type' + idx_str, 'idx' + idx_str, 'depth' + idx_str]
        for i in range(idx):
            prior_params += ['type' + str(i), 'idx' + str(i), 'depth' + str(i)]

        problem.addConstraint(rules.same_type, prior_params)
        problem.addConstraint(rules.diff_type, prior_params)

    # @todo: There's probably efficiency gains to making these rules over
    # prefixes (see above) rather than over the whole collection at once
    problem.addConstraint(rules.same_depth_same_type, all_vars)
    problem.addConstraint(rules.stars_occupy_space, all_vars)

    for constraint in additional_constraints:
        constraint(problem.addConstraint, all_vars)

    return [Solution(solution) for solution in problem.getSolutions()]

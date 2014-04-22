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


def derive_depths(marker_chars):
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

    solPrint(problem.getSolutions())
    solutions = []
    for solution in problem.getSolutions():
        solutions.append(
            [(solution['type' + str(i)], solution['depth' + str(i)])
             for i in range(len(marker_chars))])
    return solutions



#organize(['A', '1', 'a', '*', '*', 'B'])
#organize(['*', 'c', '1', '*', 'ii', 'iii', '2', 'i', 'ii', '*', 'v', '*',
#          'vii', 'A'])

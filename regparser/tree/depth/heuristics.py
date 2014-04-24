from itertools import takewhile


def prefer_multiple_children(solutions, weight):
    result = []
    for solution in solutions:
        flags = 0
        depths = [a.depth for a in solution.assignment]
        for i, depth in enumerate(depths):
            children = takewhile(lambda d: d > depth, depths[i+1:])
            if len(filter(lambda d: d == depth + 1, children)) == 1:
                flags += 1
        result.append(solution.cp_with_penalty(weight * flags / len(depths)))
    return result

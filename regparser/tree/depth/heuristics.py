"""Set of heuristics for trimming down the set of solutions. Each heuristic
works by penalizing a solution; it's then up to the caller to grab the
solution with the least penalties."""


from itertools import takewhile


def prefer_multiple_children(solutions, weight=1.0):
    """Dock solutions which have a paragraph with exactly one child. While
    this is possible, it's unlikely."""
    result = []
    for solution in solutions:
        flags = 0
        depths = [a.depth for a in solution.assignment]
        for i, depth in enumerate(depths):
            children = takewhile(lambda d: d > depth, depths[i+1:])
            if len(filter(lambda d: d == depth + 1, children)) == 1:
                flags += 1
        result.append(solution.copy_with_penalty(weight * flags / len(depths)))
    return result

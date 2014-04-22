"""Namespace for constraints on paragraph depth discovery"""

from regparser.tree.depth import markers


def must_be(value):
    """A constraint that the given variable must match the value. Use a
    workaround for lambdas, see
    http://stackoverflow.com/questions/2295290/what-do-lambda-function-closures-capture-in-python#answer-2295372"""
    return lambda x, value=value: x == value


def type_match(marker):
    """The type of the associated variable must match its marker. Lambda
    explanation as in the above rule."""
    return lambda typ, idx, m=marker: idx < len(typ) and typ[idx] == m


def same_type(typ, idx, depth, *all_prev):
    """Constraints on sequential markers with the same marker type"""
    # Group (type, idx, depth) per marker
    all_prev = [tuple(all_prev[i:i+3]) for i in range(0, len(all_prev), 3)]

    if all_prev:
        prev_typ, prev_idx, prev_depth = all_prev[-1]

    # Rule isn't relevant because it's the first marker ...
    if not all_prev:
        return True
    # ... or the previous marker's type doesn't match (see diff_type)
    elif typ != prev_typ:
        return True
    # Continuing previous type
    #elif depth == prev_depth and idx == prev_idx + 1:
    #    return True
    # Stars can't be on the same level in sequence
    elif typ == markers.stars:
        return depth < prev_depth
    # If this marker matches *any* previous marker, we may be continuing
    # it's sequence
    else:
        for prev_type, prev_idx, prev_depth in _ancestors(all_prev):
            if (prev_type == typ and prev_depth == depth
                    and idx == prev_idx + 1):
                return True
    return False


def diff_type(typ, idx, depth, *all_prev):
    all_prev = [tuple(all_prev[i:i+3]) for i in range(0, len(all_prev), 3)]

    if not all_prev or typ == all_prev[-1][0]:
        return True     # This rule isn't relevant
    elif idx == 0 and depth == all_prev[-1][2] + 1:  
        return True     # Starting a new type
    elif typ == markers.stars:
        return (all_prev[-1][2] - depth)**2 < 2
        return True
    #    if len(all_prev) == 4 and depth == 0:
    #        print [e[0][e[1]]*e[2] for e in all_prev]
    #        print depth == all_prev[-1][2]
    #        print depth == all_prev[-1][2] + 1
    #        print "---"
    #    return depth == all_prev[-1][2] or depth == all_prev[-1][2] + 1
    elif all_prev[-1][0] == markers.stars and depth == all_prev[-1][2]:
        return True     # Stars 
    else:
        for prev_type, prev_idx, prev_depth in _ancestors(all_prev):
            if (prev_type == typ and prev_depth == depth
                    and idx == prev_idx + 1):
                return True
    return False


def same_depth_same_type(*all_vars):
    elements = [tuple(all_vars[i:i+3]) for i in range(0, len(all_vars), 3)]

    def per_level(elements, last_type=None):
        level, grouped_children = _level_and_children(elements)

        if not level:
            return True
        types = set(el[0] for el in level)
        types = list(sorted(types, key=lambda t: t == markers.stars))
        if len(types) > 2:
            return False
        if len(types) == 2 and markers.stars not in types:
            return False
        if last_type in types and last_type != markers.stars:
            return False
        for children in grouped_children:
            if not per_level(children, types[0]):
                return False
        return True

    return per_level(elements)


def stars_occupy_space(*all_vars):
    elements = [tuple(all_vars[i:i+3]) for i in range(0, len(all_vars), 3)]

    def per_level(elements):
        level, grouped_children = _level_and_children(elements)

        if not level:
            return True
        last_idx = -1
        for typ, idx, _ in level:
            if typ == markers.stars:
                last_idx += 1
            elif last_idx >= idx:
                return False
            else:
                last_idx = idx

        for children in grouped_children:
            if not per_level(children):
                return False
        return True

    return per_level(elements)


def _ancestors(all_prev):
    result = [None]*10
    for prev_type, prev_idx, prev_depth in all_prev:
        result[prev_depth] = (prev_type, prev_idx, prev_depth)
        result[prev_depth + 1:] = [None]*(10 - prev_depth)
    result = filter(bool, result)
    return result


def _level_and_children(elements):
    if not elements:
        return [], []
    depth = elements[0][2]
    level = []
    grouped_children = []
    children = []

    for el in elements:
        if el[2] == depth:
            level.append(el)
            if children:
                grouped_children.append(children)
            children = []
        else:
            children.append(el)
    if children:
        grouped_children.append(children)

    return level, grouped_children

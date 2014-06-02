"""Namespace for constraints on paragraph depth discovery"""

from regparser.tree.depth import markers


def must_be(value):
    """A constraint that the given variable must matches the value."""
    def inner(var):
        return var == value
    return inner


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
    # Stars can't be on the same level in sequence. Can only start a new
    # level if the preceding wasn't inline
    elif typ == markers.stars:
        return depth < prev_depth or (prev_idx == 1
                                      and depth == prev_depth + 1)
    # If this marker matches *any* previous marker, we may be continuing
    # it's sequence
    else:
        for prev_type, prev_idx, prev_depth in _ancestors(all_prev):
            if (prev_type == typ and prev_depth == depth
                    and idx == prev_idx + 1):
                return True
    return False


def diff_type(typ, idx, depth, *all_prev):
    """Constraints on sequential markers with differing types"""
    all_prev = [tuple(all_prev[i:i+3]) for i in range(0, len(all_prev), 3)]

    # Rule isn't relevant because it's the first marker ...
    if not all_prev:
        return True
    # ... or the previous marker's type matches (see same_type)
    elif typ == all_prev[-1][0]:
        return True
    # Starting a new type
    elif idx == 0 and depth == all_prev[-1][2] + 1:
        return True
    # Stars can't skip levels forward (e.g. _ *, _ _ _ *)
    elif typ == markers.stars:
        return all_prev[-1][2] - depth >= -1
    # If following stars and on the same level, we're good
    elif all_prev[-1][0] == markers.stars and depth == all_prev[-1][2]:
        return True     # Stars
    # If this marker matches *any* previous marker, we may be continuing
    # it's sequence
    else:
        for prev_type, prev_idx, prev_depth in _ancestors(all_prev):
            if (prev_type == typ and prev_depth == depth
                    and idx == prev_idx + 1):
                return True
    return False


def same_depth_same_type(*all_vars):
    """All markers in the same level (with the same parent) should have the
    same marker type"""
    elements = [tuple(all_vars[i:i+3]) for i in range(0, len(all_vars), 3)]

    def per_level(elements, last_type=None):
        level, grouped_children = _level_and_children(elements)

        if not level:
            return True     # Base Case

        types = set(el[0] for el in level)
        types = list(sorted(types, key=lambda t: t == markers.stars))
        if len(types) > 2:
            return False
        if len(types) == 2 and markers.stars not in types:
            return False
        if last_type in types and last_type != markers.stars:
            return False
        for children in grouped_children:           # Recurse
            if not per_level(children, types[0]):
                return False
        return True

    return per_level(elements)


def stars_occupy_space(*all_vars):
    """Star markers can't be ignored in sequence, so 1, *, 2 doesn't make
    sense for a single level, unless it's an inline star. In the inline
    case, we can think of it as 1, intro-text-to-1, 2"""
    elements = [tuple(all_vars[i:i+3]) for i in range(0, len(all_vars), 3)]

    def per_level(elements):
        level, grouped_children = _level_and_children(elements)

        if not level:
            return True     # Base Case

        last_idx = -1
        for typ, idx, _ in level:
            if typ == markers.stars:
                if idx == 0:    # STARS_TAG, not INLINE_STARS
                    last_idx += 1
            elif last_idx >= idx:
                return False
            else:
                last_idx = idx

        for children in grouped_children:           # Recurse
            if not per_level(children):
                return False
        return True

    return per_level(elements)


def depth_type_order(order):
    """Create a function which constrains paragraphs depths to a particular
    type sequence. For example, we know a priori what regtext and
    interpretation markers' order should be. Adding this constrain speeds up
    solution finding."""
    order = list(order)     # defensive copy

    def inner(constrain, all_variables):
        for i in range(0, len(all_variables) / 3):
            constrain(lambda t, d: (d < len(order)
                                    and (t in (markers.stars, order[d])
                                         or t in order[d])),
                      ('type' + str(i), 'depth' + str(i)))

    return inner


def _ancestors(all_prev):
    """Given an assignment of values, construct a list of the relevant
    parents, e.g. 1, i, a, ii, A gives us 1, ii, A"""
    result = [None]*10
    for prev_type, prev_idx, prev_depth in all_prev:
        result[prev_depth] = (prev_type, prev_idx, prev_depth)
        result[prev_depth + 1:] = [None]*(10 - prev_depth)
    result = filter(bool, result)
    return result


def _level_and_children(elements):
    """Split a list of elements into elements on the current level (i.e.
    that share the same depth as the first element) and segmented children
    (children of each of those elements)"""
    if not elements:        # Base Case
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

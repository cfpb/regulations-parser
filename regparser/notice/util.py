def prepost_pend_spaces(el):
    """FR's XML doesn't always add spaces around tags that clearly need
    them. Account for this by adding spaces around the el where needed."""
    not_append_space = """@#$(-'" \t\n"""
    not_prepend_space = """%):?!,. \t\n"""

    parent = el.getparent()
    prev = el.getprevious()
    if prev is not None:
        if prev.tail and prev.tail[-1] not in not_append_space:
            prev.tail = prev.tail + ' '
    elif parent.text and parent.text[-1] not in not_append_space:
        parent.text = parent.text + ' '

    if el.tail and el.tail[0] not in not_prepend_space:
        el.tail = ' ' + el.tail

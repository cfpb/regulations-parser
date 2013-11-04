from lxml import etree


def prepost_pend_spaces(el):
    """FR's XML doesn't always add spaces around tags that clearly need
    them. Account for this by adding spaces around the el where needed."""
    not_append_space = """@#$(-'" \t\n"""
    not_prepend_space = """%):?!,. \t\n"""
    space_added = False

    parent = el.getparent()
    prev = el.getprevious()
    if prev is not None:
        if prev.tail and prev.tail[-1] not in not_append_space:
            prev.tail = prev.tail + ' '
            space_added = True
    elif parent.text and parent.text[-1] not in not_append_space:
        parent.text = parent.text + ' '
        space_added = True

    if (el.tail and el.tail[0] not in not_prepend_space
        and (el.text or el.getchildren() or not space_added)):
        el.tail = ' ' + el.tail


def swap_emphasis_tags(el):
    """FR's XML uses a different set of tags than the standard we'd like
    (XHTML). Swap out at needed"""
    for e in el.xpath('.//E'):
        original = 'E'
        if 'T' in e.attrib:
            original = original + '-' + e.attrib['T']
            del e.attrib['T']
        e.tag = 'em'
        e.attrib['data-original'] = original
        prepost_pend_spaces(e)


def spaces_then_remove(el, tag_str):
    """FR's XML tends to not add spaces where needed, which leads to the
    removal of tags sometimes smashing together words."""
    for tag in el.xpath('.//' + tag_str):
        prepost_pend_spaces(tag)
    etree.strip_tags(el, tag_str)
    return el


def body_to_string(xml_node):
    """Create a string from the text of this node and its children (without
    the outer tag)"""
    return (xml_node.text.lstrip()
            + ''.join(etree.tostring(c) for c in xml_node)
            + xml_node.tail.rstrip())

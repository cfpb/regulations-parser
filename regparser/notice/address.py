import string

from lxml import etree


def cleanup_address_p(paragraph):
    """Function for dealing with the somewhat messy paragraphs inside an
    address block. This deals with the potential lack of spaces in the XML,
    extra E tags, and strange characters up front."""
    if paragraph.text:
        ended_with_space = paragraph.text.endswith(' ')
    else:
        ended_with_space = True
    #   Inside baseball -- adds spaces to tags that don't have them
    for child in paragraph.getchildren():
        if not child.text:
            continue

        if not ended_with_space:
            child.text = ' ' + child.text
        if child.tail and not child.tail.startswith(' '):
            child.text = child.text + ' '

        if child.tail:
            ended_with_space = child.tail.endswith(' ')
        else:
            ended_with_space = child.text.endswith(' ')
    etree.strip_tags(paragraph, 'E')
    txt = paragraph.text.strip()
    while txt and not (txt[0] in string.letters or txt[0] in string.digits):
        txt = txt[1:]
    return txt


def fetch_addresses(xml_tree):
    """Pull out address information (addresses + instructions). Final
    notices do not have addresses (as we no longer accept comments)."""
    address_nodes = xml_tree.xpath('//ADD/P')
    addresses = {}
    for p in address_nodes:
        p = cleanup_address_p(p)
        if ':' in p:
            label, content = p.split(':', 1)

            #   Instructions is the label
            if label.lower().strip() == 'instructions':
                addresses['instructions'] = ([content.strip()] +
                                             addresses.get('instructions', []))
                continue

            if content.strip() and not (label.endswith('http') or
                                        label.endswith('https')):
                addresses['methods'] = (addresses.get('methods', [])
                                        + [(label.strip(), content.strip())])
                continue
        if not addresses:
            addresses['intro'] = p
        else:
            addresses['instructions'] = (addresses.get('instructions', [])
                                         + [p])
    if addresses:
        return addresses

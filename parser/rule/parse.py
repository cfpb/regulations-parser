from parser.utils import drop_while, take_while

def find_section_by_section(xml_tree):
    """Find the section-by-section analysis of this rule"""
    xml_children = xml_tree.xpath('//SUPLINF/*')
    sxs = drop_while(xml_children, lambda el: (
        el.tag != 'HD'
        or el.get('SOURCE') != 'HD1' 
        or 'section-by-section' not in el.text.lower()))
    sxs = take_while(sxs, lambda e: e.tag != 'HD' or e.get('SOURCE') != 'HD1')
    return sxs

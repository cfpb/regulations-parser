from regparser.notice.diff import find_diffs, parse_amdpar
from regparser.notice.fields import fetch_cfr_part, fetch_simple_fields
from regparser.notice.fields import fetch_document_number, fetch_dates
from regparser.notice.fields import fetch_addresses
from regparser.notice.sxs import find_section_by_section
from regparser.notice.sxs import build_section_by_section

from lxml import etree

def build_notice(xml):
    """Given xml alone, build up a corresponding notice structure"""
    for par in xml.xpath('//AMDPAR'):
        parse_amdpar(par)
    return
    cfr_part = fetch_cfr_part(xml)

    sxs = find_section_by_section(xml)
    sxs = build_section_by_section(sxs, cfr_part)
    notice = fetch_simple_fields(xml)
    notice['document_number'] = fetch_document_number(xml)
    notice['cfr_part'] = cfr_part
    notice['section_by_section'] = sxs
    dates = fetch_dates(xml)
    if dates:
        notice['dates'] = dates
    addresses = fetch_addresses(xml)
    if addresses:
        notice['addresses'] = addresses
    find_diffs(xml)
    return notice

from lxml import etree
import requests

from regparser.notice.diff import parse_amdpar
from regparser.notice.address import fetch_addresses
from regparser.notice.sxs import find_section_by_section
from regparser.notice.sxs import build_section_by_section
from regparser.notice.util import spaces_then_remove, swap_emphasis_tags


def build_notice(cfr_title, cfr_part, fr_notice):
    """Given JSON from the federal register, create our notice structure"""
    notice = {'cfr_title': cfr_title, 'cfr_part': cfr_part}
    #   Copy over most fields
    for field in ['abstract', 'action', 'agency_names', 'comments_close_on',
                  'document_number', 'publication_date',
                  'regulation_id_numbers']:
        if fr_notice[field]:
            notice[field] = fr_notice[field]

    if fr_notice['effective_on']:
        notice['effective_on'] = fr_notice['effective_on']
        notice['initial_effective_on'] = fr_notice['effective_on']

    if fr_notice['html_url']:
        notice['fr_url'] = fr_notice['html_url']

    if fr_notice['citation']:
        notice['fr_citation'] = fr_notice['citation']

    notice['fr_volume'] = fr_notice['volume']
    notice['meta'] = {}
    for key in ('dates', 'end_page', 'start_page', 'type'):
        notice['meta'][key] = fr_notice[key]

    if fr_notice['full_text_xml_url']:
        notice_str = requests.get(fr_notice['full_text_xml_url']).content
        notice_xml = etree.fromstring(notice_str)
        process_xml(notice, notice_xml)

    return notice


def process_xml(notice, notice_xml):
    """Pull out relevant fields from the xml and add them to the notice"""

    xml_chunk = notice_xml.xpath('//FURINF/P')
    if xml_chunk:
        notice['contact'] = xml_chunk[0].text

    addresses = fetch_addresses(notice_xml)
    if addresses:
        notice['addresses'] = addresses

    sxs = find_section_by_section(notice_xml)
    sxs = build_section_by_section(sxs, notice['cfr_part'],
                                   notice['meta']['start_page'])
    notice['section_by_section'] = sxs

    context = []
    amends = []
    for par in notice_xml.xpath('//AMDPAR'):
        amend_set, context = parse_amdpar(par, context)
        amends.extend(amend_set)
    if amends:
        notice['amendments'] = amends

    add_footnotes(notice, notice_xml)

    return notice


def add_footnotes(notice, notice_xml):
    notice['footnotes'] = {}
    for child in notice_xml.xpath('//FTNT/*'):
        spaces_then_remove(child, 'PRTPAGE')
        swap_emphasis_tags(child)

        ref = child.xpath('.//SU')
        if ref:
            child.text = ref[0].tail
            child.remove(ref[0])
            content = child.text
            for cc in child:
                content += etree.tostring(cc)
            content += child.tail
            notice['footnotes'][ref[0].text] = content.strip()

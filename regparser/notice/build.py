from copy import deepcopy
from collections import defaultdict
import logging
import os
from urlparse import urlparse


from lxml import etree
import requests

from regparser.notice.address import fetch_addresses
from regparser.notice.build_appendix import parse_appendix_changes
from regparser.notice.build_interp import parse_interp_changes
from regparser.notice.diff import parse_amdpar, find_section, find_subpart
from regparser.notice.diff import new_subpart_added
from regparser.notice.diff import DesignateAmendment
from regparser.notice.dates import fetch_dates
from regparser.notice.sxs import find_section_by_section
from regparser.notice.sxs import build_section_by_section
from regparser.notice.util import spaces_then_remove, swap_emphasis_tags
from regparser.notice import changes
from regparser.tree import struct
from regparser.tree.xml_parser import reg_text
from regparser.grammar.unified import notice_cfr_p

import settings


def build_notice(cfr_title, cfr_part, fr_notice, do_process_xml=True):
    """ Given JSON from the federal register, create our notice structure """
    logging.info('building notice, title {0}, part {1}, notice {2}'.format(
        cfr_title, cfr_part, fr_notice['document_number']))
    cfr_parts = set(str(ref['part']) for ref in fr_notice['cfr_references'])
    cfr_parts.add(cfr_part)

    notice = {'cfr_title': cfr_title,
              'cfr_parts': list(cfr_parts),
              'cfr_part': cfr_part}
    notice_number = fr_notice['document_number']

    # Check for configured overrides of the FR JSON for this notice
    if notice_number in settings.FR_NOTICE_OVERRIDES:
        logging.warning("overriding FR for {}".format(notice_number))
        notice_overrides = settings.FR_NOTICE_OVERRIDES[notice_number]
        for k, v in notice_overrides.iteritems():
            fr_notice[k] = v

    # Copy over most fields
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

    if fr_notice['full_text_xml_url'] and do_process_xml:
        local_notices = _check_local_version_list(
            fr_notice['full_text_xml_url'])

        if len(local_notices) > 0:
            logging.warning("using local xml for %s",
                            fr_notice['full_text_xml_url'])
            return process_local_notices(local_notices, notice)
        else:
            logging.warning("fetching notice %s",
                            fr_notice['full_text_xml_url'])
            notice_str = requests.get(fr_notice['full_text_xml_url']).content
            return [process_notice(notice, notice_str)]
    return [notice]


def split_doc_num(doc_num, effective_date):
    """ If we have a split notice, we construct a document number
    based on the original document number and the effective date. """
    effective_date = ''.join(effective_date.split('-'))
    return '%s_%s' % (doc_num, effective_date)


def process_local_notices(local_notices, partial_notice):
    """ If we have any local notices, process them. Note that this takes into
    account split notices (a single notice split into two because of different
    effective dates"""

    notices = []

    if len(local_notices) > 1:
        # If the notice is split, pick up the effective date and the
        # CFR parts from the XML
        partial_notice['effective_on'] = None
        partial_notice['cfr_parts'] = None

    for local_notice_file in local_notices:
        with open(local_notice_file, 'r') as f:
            notice = process_notice(partial_notice, f.read())
            notices.append(notice)

    notices = set_document_numbers(notices)
    return notices


def set_document_numbers(notices):
    """ If we have multiple notices, we need to fix their document
    numbers. """

    if len(notices) > 1:
        for notice in notices:
            notice['document_number'] = split_doc_num(
                notice['document_number'], notice['effective_on'])
    return notices


def process_notice(partial_notice, notice_str):
    notice_xml = etree.fromstring(notice_str)
    notice = dict(partial_notice)
    notice_xml = preprocess_notice_xml(notice_xml)
    process_xml(notice, notice_xml)
    return notice


def _check_local_version_list(url):
    """Use any local copies (potentially with modifications of the FR XML)"""
    parsed_url = urlparse(url)
    path = parsed_url.path.replace('/', os.sep)
    notice_dir_suffix, file_name = os.path.split(path)
    for xml_path in settings.LOCAL_XML_PATHS:
        if os.path.isfile(xml_path + path):
            return [xml_path + path]
        else:
            notice_directory = xml_path + notice_dir_suffix
            if os.path.exists(notice_directory):
                notices = os.listdir(notice_directory)
                prefix = file_name.split('.')[0]
                relevant_notices = [os.path.join(notice_directory, n)
                                    for n in notices if n.startswith(prefix)]
                return relevant_notices
    return []


def process_designate_subpart(amendment):
    """ Process the designate amendment if it adds a subpart. """

    if 'Subpart' in amendment.destination:
        subpart_changes = {}

        for label in amendment.labels:
            label_id = '-'.join(label)
            subpart_changes[label_id] = {
                'action': 'DESIGNATE', 'destination': amendment.destination}
        return subpart_changes


def process_new_subpart(notice, amd_label, par):
    """ A new subpart has been added, create the notice changes. """
    subpart_changes = {}
    subpart_xml = find_subpart(par)
    subpart = reg_text.build_subpart(amd_label.label[0], subpart_xml)

    for change in changes.create_subpart_amendment(subpart):
        subpart_changes.update(change)
    return subpart_changes


def create_xmlless_changes(amended_labels, notice_changes):
    """Deletes, moves, and the like do not have an associated XML structure.
    Add their changes"""
    amend_map = changes.match_labels_and_changes(amended_labels, None)
    for label, amendments in amend_map.iteritems():
        for amendment in amendments:
            if amendment['action'] == 'DELETE':
                notice_changes.update({label: {'action': amendment['action']}})
            elif amendment['action'] == 'MOVE':
                change = {'action': amendment['action']}
                destination = [d for d in amendment['destination'] if d != '?']
                change['destination'] = destination
                notice_changes.update({label: change})
            elif amendment['action'] not in ('POST', 'PUT', 'RESERVE'):
                logging.info('NOT HANDLED: %s' % amendment['action'])


def create_xml_changes(amended_labels, section, notice_changes,
                       subpart_label=None):
    """For PUT/POST, match the amendments to the section nodes that got
    parsed, and actually create the notice changes. """

    def per_node(node):
        node.child_labels = [c.label_id() for c in node.children]
    struct.walk(section, per_node)

    amend_map = changes.match_labels_and_changes(amended_labels, section)

    for label, amendments in amend_map.iteritems():
        for amendment in amendments:
            if amendment['action'] in ('POST', 'PUT'):
                if (subpart_label and amendment['action'] == 'POST'
                        and len(label.split('-')) == 2):
                    amendment['extras'] = {'subpart': subpart_label}
                if 'field' in amendment:
                    nodes = changes.create_field_amendment(label, amendment)
                else:
                    nodes = changes.create_add_amendment(amendment)
                for n in nodes:
                    notice_changes.update(n)
            elif amendment['action'] == 'RESERVE':
                change = changes.create_reserve_amendment(amendment)
                notice_changes.update(change)
            elif amendment['action'] not in ('DELETE', 'MOVE'):
                logging.info('NOT HANDLED: %s' % amendment['action'])


class AmdparByParent(object):
    """Not all AMDPARs have a single REGTEXT/etc. section associated with them,
    particularly for interpretations/appendices. This simple class wraps those
    fields"""
    def __init__(self, parent, first_amdpar):
        self.parent = parent
        self.amdpars = [first_amdpar]

    def append(self, next_amdpar):
        self.amdpars.append(next_amdpar)


def preprocess_notice_xml(notice_xml):
    """Unfortunately, the notice xml is often inaccurate. This function
    attempts to fix some of those (general) flaws. For specific issues, we
    tend to instead use the files in settings.LOCAL_XML_PATHS"""
    notice_xml = deepcopy(notice_xml)   # We will be destructive

    # Last amdpar in a section; probably meant to add the amdpar to the
    # next section
    for amdpar in notice_xml.xpath("//AMDPAR"):
        if amdpar.getnext() is None:
            parent = amdpar.getparent()
            next_parent = parent.getnext()
            if (next_parent is not None
                    and parent.get('PART') == next_parent.get('PART')):
                parent.remove(amdpar)
                next_parent.insert(0, amdpar)

    # Supplement I AMDPARs are often incorrect (labelled as Ps)
    xpath_contains_supp = "contains(., 'Supplement I')"
    xpath = "//REGTEXT//HD[@SOURCE='HD1' and %s]" % xpath_contains_supp
    for supp_header in notice_xml.xpath(xpath):
        parent = supp_header.getparent()
        if (parent.xpath("./AMDPAR[%s]" % xpath_contains_supp)
                or parent.xpath("./P[%s]" % xpath_contains_supp)):
            pred = supp_header.getprevious()
            while pred is not None:
                if pred.tag not in ('P', 'AMDPAR'):
                    pred = pred.getprevious()
                else:
                    pred.tag = 'AMDPAR'
                    if 'supplement i' in pred.text.lower():
                        pred = None
                    else:
                        pred = pred.getprevious()

    # Clean up emphasized paragraph tags
    for par in notice_xml.xpath("//P/*[position()=1 and name()='E']/.."):
        em = par.getchildren()[0]   # must be an E from the xpath

        #   wrap in a thunk to delay execution
        par_text = lambda: par.text or ""
        em_text, em_tail = lambda: em.text or "", lambda: em.tail or ""

        par_open = par_text()[-1:] == "("
        em_open = em_text()[:1] == "("
        em_txt_closed = em_text()[-1:] == ")"
        em_tail_closed = em_tail()[:1] == ")"

        if (par_open or em_open) and (em_txt_closed or em_tail_closed):
            if not par_open and em_open:                # Move '(' out
                par.text = par_text() + "("
                em.text = em_text()[1:]

            if not em_tail_closed and em_txt_closed:    # Move ')' out
                em.text = em_text()[:-1]
                em.tail = ")" + em_tail()

    return notice_xml


def process_amendments(notice, notice_xml):
    """ Process the changes to the regulation that are expressed in the notice.
    """
    amends = []
    notice_changes = changes.NoticeChanges()

    amdpars_by_parent = []
    for par in notice_xml.xpath('//AMDPAR'):
        parent = par.getparent()
        exists = filter(lambda aXp: aXp.parent == parent, amdpars_by_parent)
        if exists:
            exists[0].append(par)
        else:
            amdpars_by_parent.append(AmdparByParent(parent, par))

    default_cfr_part = notice['cfr_part']
    for aXp in amdpars_by_parent:
        amended_labels = []
        designate_labels, other_labels = [], []
        context = [default_cfr_part]
        for par in aXp.amdpars:
            als, context = parse_amdpar(par, context)
            amended_labels.extend(als)

            labels_by_part = defaultdict(list)
            for al in amended_labels:
                if isinstance(al, DesignateAmendment):
                    subpart_changes = process_designate_subpart(al)
                    if subpart_changes:
                        notice_changes.update(subpart_changes)
                    designate_labels.append(al)
                elif new_subpart_added(al):
                    notice_changes.update(process_new_subpart(notice, al, par))
                    designate_labels.append(al)
                else:
                    other_labels.append(al)
                    labels_by_part[al.label[0]].append(al)

            create_xmlless_changes(other_labels, notice_changes)

            # for cfr_part, rel_labels in labels_by_part.iteritems():
            labels_for_part = {part: labels
                               for part, labels in labels_by_part.iteritems()
                               if part == default_cfr_part}
            print(labels_for_part)
            for cfr_part, rel_labels in labels_for_part.iteritems():
                section_xml = find_section(par)
                if section_xml is not None:
                    subparts = aXp.parent.xpath('.//SUBPART/HD')
                    if subparts:
                        subpart_label = [cfr_part, 'Subpart',
                                         subparts[0].text[8:9]]
                    else:
                        subpart_label = None

                    for section in reg_text.build_from_section(cfr_part,
                                                               section_xml):
                        create_xml_changes(rel_labels, section, notice_changes,
                                           subpart_label)

                for appendix in parse_appendix_changes(rel_labels, cfr_part,
                                                       aXp.parent):
                    create_xml_changes(rel_labels, appendix, notice_changes)

                interp = parse_interp_changes(rel_labels, cfr_part, aXp.parent)
                if interp:
                    create_xml_changes(rel_labels, interp, notice_changes)

            amends.extend(designate_labels)
            amends.extend(other_labels)

            # if other_labels:    # Carry cfr_part through amendments
            #    default_cfr_part = other_labels[-1].label[0]

    if amends:
        notice['amendments'] = amends
        notice['changes'] = notice_changes.changes
    elif notice['document_number'] in settings.REISSUANCES:
        notice['changes'] = {
            default_cfr_part: [{
                'action': 'PUT',
                'node': reg_text.build_tree(notice_xml)
            }]
        }


def process_sxs(notice, notice_xml):
    """ Find and build SXS from the notice_xml. """
    sxs = find_section_by_section(notice_xml)
    # note we will continue to use cfr_parts[0] as the default SxS label until
    # we find a counter example
    sxs = build_section_by_section(sxs, notice['meta']['start_page'],
                                   notice['cfr_parts'][0])
    notice['section_by_section'] = sxs


def fetch_cfr_parts(notice_xml):
    """ Sometimes we need to read the CFR part numbers from the notice
        XML itself. This would need to happen when we've broken up a
        multiple-effective-date notice that has multiple CFR parts that
        may not be included in each date. """
    cfr_elm = notice_xml.xpath('//CFR')[0]
    results = notice_cfr_p.parseString(cfr_elm.text)
    return list(results)


def process_xml(notice, notice_xml):
    """Pull out relevant fields from the xml and add them to the notice"""

    xml_chunk = notice_xml.xpath('//FURINF/P')
    if xml_chunk:
        notice['contact'] = xml_chunk[0].text

    addresses = fetch_addresses(notice_xml)
    if addresses:
        notice['addresses'] = addresses

    if not notice.get('effective_on'):
        dates = fetch_dates(notice_xml)
        if dates and 'effective' in dates:
            notice['effective_on'] = dates['effective'][0]

    if not notice.get('cfr_parts'):
        cfr_parts = fetch_cfr_parts(notice_xml)
        notice['cfr_parts'] = cfr_parts

    process_sxs(notice, notice_xml)
    process_amendments(notice, notice_xml)
    add_footnotes(notice, notice_xml)

    return notice


def add_footnotes(notice, notice_xml):
    """ Parse the notice xml for footnotes and add them to the notice. """
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

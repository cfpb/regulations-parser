from copy import deepcopy
from itertools import dropwhile
import logging

from regparser.notice.diff import DesignateAmendment
from regparser.tree.struct import Node
from regparser.tree.xml_parser.appendices import process_appendix


def _is_appendix_amend(al):
    """Serves as a guard/filter to distinguish appendix amendments from
    amendments to other parts of the reg"""
    return (not isinstance(al, DesignateAmendment)
            and Node.INTERP_MARK not in al.label
            and len(al.label) > 1
            and not al.label[1].isdigit())


def parse_appendix_changes(amended_labels, cfr_part, parent_xml):
    """Entry point. Currently only processes whole appendices, though the
    functionality will expand in the future"""
    relevant_amends = [al for al in amended_labels if _is_appendix_amend(al)]
    appendices = {}
    for al in relevant_amends:
        cfr_part, letter = al.label[:2]
        #   Whole appendix, e.g. "1234-C" or appendix section, e.g. "1234-C-12"
        if len(al.label) <= 3 and letter not in appendices:
            appendix = whole_appendix(parent_xml, cfr_part, letter)
            appendices[letter] = appendix
    return [a for a in appendices.values() if a]


def whole_appendix(xml, cfr_part, letter):
    """Attempt to parse an appendix. Used when the entire appendix has been
    replaced/added or when we can use the section headers to determine our
    place. If the format isn't what we expect, display a warning."""
    xml = deepcopy(xml)
    hds = xml.xpath('//HD[contains(., "Appendix %s to Part %s")]'
                    % (letter, cfr_part))
    if len(hds) == 0:
        logging.warning("Could not find Appendix %s to part %s"
                        % (letter, cfr_part))
    elif len(hds) > 1:
        logging.warning("Too many headers for %s to part %s"
                        % (letter, cfr_part))
    else:
        hd = hds[0]
        hd.set('SOURCE', 'HED')
        extract = hd.getnext()
        if extract is not None and extract.tag == 'EXTRACT':
            extract.insert(0, hd)
            for trailing in dropwhile(lambda n: n.tag != 'AMDPAR',
                                      extract.getchildren()):
                extract.remove(trailing)
            return process_appendix(extract, cfr_part)
        logging.warning("Bad format for whole appendix")

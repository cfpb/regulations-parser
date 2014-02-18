from copy import deepcopy
from itertools import dropwhile
import logging

from regparser.notice.diff import DesignateAmendment
from regparser.tree.struct import Node
from regparser.tree.xml_parser.appendices import process_appendix


def _is_appendix_amend(al):
    return (not isinstance(al, DesignateAmendment)
            and not Node.INTERP_MARK in al.label
            and len(al.label) > 1
            and not al.label[1].isdigit())


def parse_appendix_changes(amended_labels, cfr_part, parent_xml):
    relevant_amends = [al for al in amended_labels if _is_appendix_amend(al)]
    appendices = []
    for al in relevant_amends:
        if len(al.label) == 2 and al.field is None:
            appendix = whole_appendix(parent_xml, al.label[0], al.label[1])
            if appendix:
                appendices.append(appendix)
    return appendices


def whole_appendix(xml, cfr_part, letter):
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

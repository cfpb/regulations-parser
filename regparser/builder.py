import copy

from regparser import api_writer, content
from regparser.federalregister import fetch_notices
from regparser.history.notices import (
    applicable as applicable_notices, group_by_eff_date)
from regparser.history.delays import modify_effective_dates
from regparser.layer import (
    external_citations, formatting, graphics, key_terms, internal_citations,
    interpretations, meta, paragraph_markers, section_by_section,
    table_of_contents, terms)
from regparser.notice.compiler import compile_regulation
from regparser.tree.build import build_whole_regtree
from regparser.tree.xml_parser import reg_text


class Builder(object):
    """Methods used to build all versions of a single regulation, their
    layers, etc. It is largely glue code"""

    def __init__(self, cfr_title, cfr_part, doc_number):
        self.cfr_title = cfr_title
        self.cfr_part = cfr_part
        self.doc_number = doc_number
        self.writer = api_writer.Client()

        self.notices = fetch_notices(self.cfr_title, self.cfr_part)
        modify_effective_dates(self.notices)
        #   Only care about final
        self.notices = [n for n in self.notices if 'effective_on' in n]
        self.eff_notices = group_by_eff_date(self.notices)

    def write_notices(self):
        for notice in self.notices:
            #  No need to carry this around
            del notice['meta']
            self.writer.notice(notice['document_number']).write(notice)

    def write_regulation(self, reg_tree):
        self.writer.regulation(self.cfr_part, self.doc_number).write(reg_tree)

    def gen_and_write_layers(self, reg_tree, act_info):
        for ident, layer_class in (
                ('external-citations',
                    external_citations.ExternalCitationParser),
                ('meta', meta.Meta),
                ('analyses', section_by_section.SectionBySection),
                ('internal-citations',
                    internal_citations.InternalCitationParser),
                ('toc', table_of_contents.TableOfContentsLayer),
                ('interpretations', interpretations.Interpretations),
                ('terms', terms.Terms),
                ('paragraph-markers', paragraph_markers.ParagraphMarkers),
                ('keyterms', key_terms.KeyTerms),
                ('formatting', formatting.Formatting),
                ('graphics', graphics.Graphics)):
            layer = layer_class(reg_tree, self.cfr_title, self.doc_number,
                                self.notices, act_info).build()
            self.writer.layer(ident, self.cfr_part, self.doc_number).write(
                layer)

    def revision_generator(self, reg_tree):
        relevant_notices = []
        for date in sorted(self.eff_notices.keys()):
            relevant_notices.extend(
                n for n in self.eff_notices[date]
                if 'changes' in n and n['document_number'] != self.doc_number)

        for notice in relevant_notices:
            version = notice['document_number']
            old_tree = reg_tree
            merged_changes = self.merge_changes(version, notice['changes'])
            reg_tree = compile_regulation(old_tree, merged_changes)
            yield version, old_tree, reg_tree

    def merge_changes(self, document_number, changes):
        patches = content.RegPatches().get(document_number)
        if patches:
            changes = copy.copy(changes)
            for key in patches:
                if key in changes:
                    changes[key].extend(patches[key])
                else:
                    changes[key] = patches[key]
        return changes

    @staticmethod
    def reg_tree(reg_str):
        if reg_str[:1] == '<':  # XML
            return reg_text.build_tree(reg_str)
        else:
            return build_whole_regtree(reg_str)

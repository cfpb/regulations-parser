import codecs
import copy
import hashlib
import os
import pickle
import re
import logging

from lxml import etree

from regparser import api_writer, content
from regparser.federalregister import fetch_notice_json, fetch_notices
from regparser.history.notices import (
    applicable as applicable_notices, group_by_eff_date)
from regparser.history.delays import modify_effective_dates
from regparser.layer import (
    external_citations, formatting, graphics, key_terms, internal_citations,
    interpretations, meta, paragraph_markers, section_by_section,
    table_of_contents, terms)
from regparser.notice.compiler import compile_regulation
from regparser.notice.build import build_notice
from regparser.tree import struct
# from regparser.tree.build import build_whole_regtree
from regparser.tree.xml_parser import reg_text
from regparser.diff.tree import changes_between
from regparser.tree.struct import FrozenNode


class Builder(object):
    """Methods used to build all versions of a single regulation, their
    layers, etc. It is largely glue code"""

    def __init__(self, cfr_title, cfr_part, doc_number, checkpointer=None,
                 writer_type=None):
        self.cfr_title = cfr_title
        self.cfr_part = cfr_part
        self.doc_number = doc_number
        self.checkpointer = checkpointer or NullCheckpointer()
        self.writer = api_writer.Client(writer_type=writer_type)
        self.notices_json = []
        self.notices = []
        self.notice_doc_numbers = []
        self.eff_notices = []

    def fetch_notices_json(self):
        self.notices_json = fetch_notice_json(self.cfr_title, self.cfr_part,
                                              only_final=True)
        self.notice_doc_numbers = [notice_json['document_number']
                                   for notice_json in self.notices_json]

    def build_single_notice(self, notice_json, checkpoint=True):
        logging.info('building notice {0} from {1}'.format(
            notice_json['document_number'], notice_json['full_text_xml_url']))
        if checkpoint:
            notice = self.checkpointer.checkpoint(
                'notice-' + notice_json['document_number'],
                lambda: build_notice(self.cfr_title, self.cfr_part,
                                     notice_json)
            )
        else:
            notice = build_notice(self.cfr_title, self.cfr_part, notice_json)

        return notice

    def build_notice_from_doc_number(self, doc_number, checkpoint=True):
        if doc_number in self.notice_doc_numbers:
            notice_json = [notice for notice in self.notices_json
                           if notice['document_number'] == doc_number][0]
            notice = self.build_single_notice(notice_json, checkpoint)
            self.notices.extend(notice)
            self.eff_notices = group_by_eff_date(self.notices)
            return notice

    def build_notices(self, checkpoint=True):
        for result in self.notices_json:
            notice = self.build_single_notice(result, checkpoint)
            self.notices.extend(notice)
        modify_effective_dates(self.notices)
        #   Only care about final
        self.notices = [n for n in self.notices if 'effective_on' in n]
        self.eff_notices = group_by_eff_date(self.notices)

        self.eff_notices = self.checkpointer.checkpoint(
            "effective-notices",
            lambda: notices_for_cfr_part(self.cfr_title, self.cfr_part)
        )
        self.notices = []
        for notice_group in self.eff_notices.values():
            self.notices.extend(notice_group)

    def write_notices(self):
        for notice in self.notices:
            #  No need to carry this around
            del notice['meta']
            self.writer.notice(
                self.cfr_part, notice['document_number']).write(notice)

    def write_notice(self, doc_number, old_tree=None, reg_tree=None,
                     layers=None, last_version=''):
        """ Write a single notice out. For the XMLWriter, we need to
            include the reg_tree for the notice. """
        # Get the notice by doc number
        notice = next((n for n in self.notices
                       if n['document_number'] == doc_number), None)

        # We can optionall write out the diffs with the notice if we're
        # given the old tree.
        changes = {}
        if old_tree is not None and reg_tree is not None:
            # FrozenNode and Node are not API-compatible. This is
            # troublesome.
            changes = dict(changes_between(
                FrozenNode.from_node(old_tree),
                FrozenNode.from_node(reg_tree)))

        # Write the notice
        writer = self.writer.notice(self.cfr_part,
                                    self.doc_number,
                                    notices=self.notices,
                                    layers=layers)
        writer.write(notice, changes=changes, reg_tree=reg_tree,
                     left_doc_number=last_version)

    def write_regulation(self, reg_tree, layers=None):
        self.writer.regulation(self.cfr_part,
                               self.doc_number,
                               notices=self.notices,
                               layers=layers).write(reg_tree)

    def generate_layers(self, reg_tree, act_info, cache, notices=None):
        layers = {}
        if notices is None:
            notices = applicable_notices(self.notices, self.doc_number)
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
            layer = self.checkpointer.checkpoint(
                ident + "-" + self.doc_number,
                lambda: layer_class(
                    reg_tree, self.cfr_title, self.doc_number, notices,
                    act_info).build(cache.cache_for(ident)))
            layers[ident] = layer

        return layers

    def write_layers(self, layers):
        for ident, layer in layers.items():
            self.writer.layer(ident, self.cfr_part,
                              self.doc_number).write(layer)

    def gen_and_write_layers(self, reg_tree, act_info, cache, notices=None):
        layers = self.generate_layers(reg_tree, act_info, cache, notices)
        self.write_layers(layers)

    def revision_generator(self, reg_tree):
        """Given an initial regulation tree, this will emit (and checkpoint)
        new versions of the tree, along with the notice that caused the
        change. This is a generator, so processing only occurs as needed"""
        for version, merged_changes in self.changes_in_sequence():
            old_tree = reg_tree
            reg_tree = self.checkpointer.checkpoint(
                "compiled-" + version,
                lambda: compile_regulation(old_tree, merged_changes))
            notices = applicable_notices(self.notices, version)
            first_notice = None
            for notice in notices:
                if notice['document_number'] == version:
                    first_notice = notice
            yield first_notice, old_tree, reg_tree, notices

    def changes_in_sequence(self):
        """Generator of version string, changes-object pairs. This can be used
        to see what changes will be applied going forward."""
        relevant_notices = []
        for date in sorted(self.eff_notices.keys()):
            relevant_notices.extend(
                n for n in self.eff_notices[date]
                if 'changes' in n and n['document_number'] != self.doc_number)
        for notice in relevant_notices:
            version = notice['document_number']
            yield version, self.merge_changes(version, notice['changes'])

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
            raise ValueError("Building from text input is no longer "
                             "supported")
            # return build_whole_regtree(reg_str)

    @staticmethod
    def determine_doc_number(reg_str, title, title_part):
        """Instead of requiring the user provide a doc number, we can find it
        within the xml file"""
        # @todo: remove the double-conversion
        reg_xml = etree.fromstring(reg_str)
        doc_number = _fr_doc_to_doc_number(reg_xml)
        if not doc_number:
            doc_number = _fdsys_to_doc_number(reg_xml, title, title_part)
        return doc_number


class LayerCacheAggregator(object):
    """A lot of the reg tree remains the same between versions; we don't
    want to recompute layers every time. This object keeps track of what
    labels are seen/valid."""
    def __init__(self):
        self._known_labels = set()
        self._caches = {}

    def invalidate(self, labels):
        """Given a list of labels, clear out any known labels that would be
        affected. For subpart changes, we just wipe out the whole cache. If
        removing an interpretation, make the logic easier by removing
        related regtext as well."""
        if any('Subpart' in label for label in labels):
            self._known_labels = set()
        else:
            stripped = []
            for label in labels:
                if struct.Node.INTERP_MARK in label:
                    idx = label.find(struct.Node.INTERP_MARK) - 1
                    stripped.append(label[:idx])
                else:
                    stripped.append(label)
            self._known_labels = set(
                known for known in self._known_labels
                if not any(known.startswith(l) for l in stripped))

    def invalidate_by_notice(self, notice):
        """Using the notice structure, invalidate based on the 'changes'
        field"""
        self.invalidate([key for key in notice.get('changes', {})])
        patches = content.RegPatches().get(notice['document_number'], {})
        self.invalidate(patches.keys())

    def is_known(self, label):
        return label in self._known_labels

    def replace_using(self, tree):
        """Clear out the known labels; replace them using the provided node
        tree."""
        self._known_labels = set()

        def per_node(node):
            self._known_labels.add(node.label_id())
        struct.walk(tree, per_node)

    def cache_for(self, layer_name):
        """Get a LayerCache object for a given layer name. Not all layers
        have caches, as caches are currently only used for layers that
        depend on the node's text"""
        if layer_name in ('external-citations', 'internal-citations',
                          'interpretations', 'paragraph-markers', 'keyterms',
                          'formatting', 'graphics'):
            if layer_name not in self._caches:
                self._caches[layer_name] = LayerCache(self)
            return self._caches[layer_name]
        else:
            return EmptyCache()


def notices_for_cfr_part(title, part):
    """Retrieves all final notices for a title-part pair, orders them, and
    returns them as a dict[effective_date_str] -> list(notices)"""
    notices = fetch_notices(title, part, only_final=True)
    modify_effective_dates(notices)
    return group_by_eff_date(notices)


def _fr_doc_to_doc_number(xml):
    """Pull out a document number from an FR document, i.e. a notice"""
    frdoc_els = xml.xpath('//FRDOC')
    if len(frdoc_els) > 0:
        frdoc_pieces = frdoc_els[0].text.split()
        if len(frdoc_pieces) > 2 and frdoc_pieces[:2] == ['[FR', 'Doc.']:
            return frdoc_pieces[2]


def _fdsys_to_doc_number(xml, title, title_part):
    """Pull out a document number from an FDSYS document, i.e. an annual
    edition of a reg"""
    original_date_els = xml.xpath('//FDSYS/ORIGINALDATE')
    if len(original_date_els) > 0:
        date = original_date_els[0].text
        #   Grab oldest document number from Federal register API
        notices = fetch_notice_json(title, title_part, only_final=True,
                                    max_effective_date=date)
        if notices:
            return notices[0]['document_number']


class LayerCache(object):
    """Keeps a cache of a single layer. Used in combination with a
    LayerCacheAggregator to determine when something needs to be recomputed."""
    def __init__(self, parent):
        self.parent = parent
        self._cache = {}

    def fetch_or_process(self, layer, node):
        """Retrieve the value of a layer if known. Otherwise, compute the
        value and cache the result"""
        label = node.label_id()
        if not self.parent.is_known(label):
            self._cache[label] = layer.process(node)
        return self._cache.get(label)


class EmptyCache(object):
    """Dummy cache used to represent layers that should not be cached. For
    example, the toc layer depends on more than the text of its associated
    node, so it should not be cached."""
    def fetch_or_process(self, layer, node):
        return layer.process(node)


def _serialize_xml_fields(node):
    if node.source_xml is not None:
        node.source_xml = etree.tostring(node.source_xml)


def _deserialize_xml_fields(node):
    if node.source_xml:
        node.source_xml = etree.fromstring(node.source_xml)


class Checkpointer(object):
    """Save checkpoints during the build pipeline. Generally, a caller will
    specify, a unique tag (a string) and a fallback function (for how to
    compute it when there is no checkpoint). Calling checkpoint increment the
    counter field, which is prefixed to the filename to limit the risk of
    re-ordering collisions."""
    def __init__(self, file_path):
        self.counter = 0
        self.file_path = file_path
        self.suffix = ""
        self.ignore_checkpoints = False
        if not os.path.isdir(file_path):
            os.makedirs(file_path)

    def _filename(self, tag):
        """Combine the counter and tag name to create a filename"""
        name = str(self.counter).zfill(6) + ":"
        name += re.sub(r"\s", "", tag.lower())
        name += self.suffix + ".p"
        return os.path.join(self.file_path, name)

    def _serialize(self, tag, obj):
        """Performs class-specific conversions before writing to a file"""
        if isinstance(obj, struct.Node):
            obj = copy.deepcopy(obj)
            struct.walk(obj, _serialize_xml_fields)

        with open(self._filename(tag), 'wb') as to_write:
            pickle.dump(obj, to_write)

    def _deserialize(self, tag):
        """Attempts to read the object from disk. Performs class-specific
        conversions when deserializing"""
        name = self._filename(tag)
        if os.path.exists(name):
            with open(name, 'rb') as to_read:
                try:
                    obj = pickle.load(to_read)
                except Exception:   # something bad happened during unpickling
                    obj = None

            if isinstance(obj, struct.Node):
                struct.walk(obj, _deserialize_xml_fields)
            return obj

    def _reset(self):
        """Used for testing"""
        self.counter = 0
        self.ignore_checkpoints = False

    def checkpoint(self, tag, fn, force=False):
        """Primary interface for storing an object"""
        self.counter += 1
        existing = self._deserialize(tag)
        if not force and existing is not None and not self.ignore_checkpoints:
            return existing
        else:
            result = fn()
            self._serialize(tag, result)
            self.ignore_checkpoints = True
            return result


class NullCheckpointer(object):
    def checkpoint(self, tag, fn, force=False):
        return fn()


def tree_and_builder(filename, title, checkpoint_path=None,
                     writer_type=None, doc_number=None):
    """Reads the regulation file and parses it. Returns the resulting tree as
    well as a Builder object for further manipulation. Looks up the doc_number
    if it's not provided"""
    if checkpoint_path is None:
        checkpointer = NullCheckpointer()
    else:
        checkpointer = Checkpointer(checkpoint_path)

    reg_text = ''
    with codecs.open(filename, 'r', 'utf-8') as f:
        reg_text = f.read()
    file_digest = hashlib.sha256(reg_text.encode('utf-8')).hexdigest()

    reg_tree = checkpointer.checkpoint("init-tree-" + file_digest,
                                       lambda: Builder.reg_tree(reg_text))
    title_part = reg_tree.label_id()
    if doc_number is None:
        doc_number = checkpointer.checkpoint(
            "doc-number-" + file_digest,
            lambda: Builder.determine_doc_number(reg_text, title, title_part))
    if not doc_number:
        raise ValueError("Could not determine document number")

    checkpointer.suffix = ":".join(["", title_part, str(title), doc_number])

    builder = Builder(cfr_title=title,
                      cfr_part=title_part,
                      doc_number=doc_number,
                      checkpointer=checkpointer,
                      writer_type=writer_type)
    builder.fetch_notices_json()
    builder.build_notices()

    return reg_tree, builder

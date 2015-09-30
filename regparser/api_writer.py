import os
import os.path
import shutil
import hashlib

from git import Repo
from git.exc import InvalidGitRepositoryError
from lxml.etree import Element, SubElement

import requests

from regparser.tree.struct import Node, NodeEncoder
from regparser.notice.encoder import AmendmentEncoder
from regparser.tree.xml_parser.reg_text import get_markers
from lxml.etree import tostring, fromstring

from utils import set_of_random_letters, interpolate_string

import settings


class AmendmentNodeEncoder(AmendmentEncoder, NodeEncoder):
    pass


class FSWriteContent:
    """This writer places the contents in the file system """

    def __init__(self, path):
        self.path = path

    def write(self, python_obj):
        """Write the object as json to disk"""
        path_parts = self.path.split('/')
        dir_path = settings.OUTPUT_DIR + os.path.join(*path_parts[:-1])

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        full_path = settings.OUTPUT_DIR + os.path.join(*path_parts)
        with open(full_path, 'w') as out:
            text = AmendmentNodeEncoder(
                sort_keys=True, indent=4,
                separators=(', ', ': ')).encode(python_obj)
            out.write(text)


class APIWriteContent:
    """This writer writes the contents to the specified API"""
    def __init__(self, path):
        self.path = path

    def write(self, python_obj):
        """Write the object (as json) to the API"""
        requests.post(
            settings.API_BASE + self.path,
            data=AmendmentNodeEncoder().encode(python_obj),
            headers={'content-type': 'application/json'})


class GitWriteContent:
    """This writer places the content in a git repo on the file system"""
    def __init__(self, path):
        self.path = path

    def folder_name(self, node):
        """Directories are generally just the last element a node's label,
        but subparts and interpretations are a little special."""
        if node.node_type == Node.SUBPART:
            return '-'.join(node.label[-2:])
        elif len(node.label) > 2 and node.label[-1] == Node.INTERP_MARK:
            return '-'.join(node.label[-2:])
        else:
            return node.label[-1]

    def write_tree(self, root_path, node):
        """Given a file system path and a node, write the node's contents and
        recursively write its children to the provided location."""
        if not os.path.exists(root_path):
            os.makedirs(root_path)

        node_text = u"---\n"
        if node.title:
            node_text += 'title: "' + node.title + '"\n'
        node_text += 'node_type: ' + node.node_type + '\n'
        child_folders = [self.folder_name(child) for child in node.children]

        node_text += 'children: ['
        node_text += ', '.join('"' + f + '"' for f in child_folders)
        node_text += ']\n'

        node_text += '---\n' + node.text
        with open(root_path + os.sep + 'index.md', 'w') as f:
            f.write(node_text.encode('utf8'))

        for idx, child in enumerate(node.children):
            child_path = root_path + os.sep + child_folders[idx]
            shutil.rmtree(child_path, ignore_errors=True)
            self.write_tree(child_path, child)

    def write(self, python_object):
        if "regulation" in self.path:
            path_parts = self.path.split('/')
            dir_path = settings.GIT_OUTPUT_DIR + os.path.join(*path_parts[:-1])

            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

            try:
                repo = Repo(dir_path)
            except InvalidGitRepositoryError:
                repo = Repo.init(dir_path)
                repo.index.commit("Initial commit for " + path_parts[-2])

            # Write all files (and delete any old ones)
            self.write_tree(dir_path, python_object)
            # Add and new files to git
            repo.index.add(repo.untracked_files)
            # Delete and modify files as needed
            deleted, modified = [], []
            for diff in repo.index.diff(None):
                if diff.deleted_file:
                    deleted.append(diff.a_blob.path)
                else:
                    modified.append(diff.a_blob.path)
            if modified:
                repo.index.add(modified)
            if deleted:
                repo.index.remove(deleted)
            # Commit with the notice id as the commit message
            repo.index.commit(path_parts[-1])


class XMLWriteContent:

    def __init__(self, path, layers=None):
        self.path = path
        self.layers = layers
        self.layers['definitions'] = self.extract_definitions()
        self.appendix_sections = 1 # need to track these manually

        path_parts = self.path.split('/')
        dir_path = settings.OUTPUT_DIR + os.path.join(*path_parts[:-1])

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        full_path = settings.OUTPUT_DIR + os.path.join(*path_parts)
        self.full_path = full_path

    def write(self, tree):
        xml_head = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_tree = self.to_xml(tree)
        xml_string = xml_head + tostring(xml_tree, pretty_print=True)

        with open(self.full_path, 'w') as f:
            f.write(xml_string)

    def extract_definitions(self):

        defs = self.layers['terms']['referenced']
        references = {}
        for _, defn in defs.items():
            ref_node_label = defn['reference']
            ref_offsets = defn['position']
            term = defn['term']
            defn_dict = {'offset': ref_offsets,
                         'term': term}
            references[ref_node_label] = defn_dict

        return references

    @staticmethod
    def apply_terms(text, replacements):

        replacement_texts = []
        replacement_offsets = []
        for repl in replacements:
            repl_text = repl['ref']
            offsets = repl['offsets']
            replacement_offsets.extend(offsets)
            for offset in offsets:
                replacement = text[offset[0]:offset[1]]
                repl_target = repl_text.split(':')[1]
                replacement = '<ref target="{}">'.format(repl_target) + replacement + '</ref>'
                replacement_texts.append(replacement)

        return replacement_offsets, replacement_texts

    @staticmethod
    def apply_paragraph_markers(text, replacements):

        replacement_texts = []
        replacement_offsets = []
        for i, repl in enumerate(replacements):
            marker_text = repl['text']
            marker_length = len(marker_text)
            marker_locations = repl['locations']
            for loc in marker_locations:
                offset = [loc, loc + marker_length]
                replacement_offsets.append(offset)
                replacement_texts.append('')

        return replacement_offsets, replacement_texts

    @staticmethod
    def apply_internal_citations(text, replacements):

        replacement_texts = []
        replacement_offsets = []
        for repl in replacements:
            citation = repl['citation']
            offsets = repl['offsets']
            citation_target = '-'.join(citation)
            for offset in offsets:
                ref_text = text[offset[0]:offset[1]]
                replacement_text = '<ref target="{}" reftype="internal">'.format(citation_target) + ref_text + '</ref>'
                replacement_offsets.append(offset)
                replacement_texts.append(replacement_text)

        return replacement_offsets, replacement_texts

    @staticmethod
    def apply_external_citations(text, replacements):

        replacement_texts = []
        replacement_offsets = []
        for repl in replacements:
            citation = repl['citation']
            citation_type = repl['citation_type']
            offsets = repl['offsets']
            for offset in offsets:
                ref_text = text[offset[0]:offset[1]]
                # we need to form a URL for the external citation based on the citation type
                # I don't know how to do that yet so the target is just a placeholder
                target_url = '{}:{}'.format(citation_type, '-'.join(citation))
                replacement_text = '<ref target="{}" reftype="external">'.format(target_url) + ref_text + '</ref>'
                replacement_texts.append(replacement_text)
                replacement_offsets.append(offset)

        return replacement_offsets, replacement_texts

    @staticmethod
    def apply_definitions(text, replacement):

        offset = replacement['offset']
        term = replacement['term']
        hash_value = hashlib.sha1(term).hexdigest()
        replacement_text = text[offset[0]:offset[1]]
        replacement_text = '<def term="{}" id="{}">'.format(term, hash_value) + replacement_text + '</def>'

        return [offset], [replacement_text]


    @staticmethod
    def apply_keyterms():
        pass

    @staticmethod
    def apply_formatting():
        pass

    def fdsys(self, reg_number, date='2012-01-01', orig_date='2012-01-01'):
        meta = self.layers['meta'][reg_number][0]
        elem = Element('fdsys')
        cfr_title_num = SubElement(elem, 'cfrTitleNum')
        cfr_title_num.text = str(meta['cfr_title_number'])
        cfr_title_text = SubElement(elem, 'cfrTitleText')
        cfr_title_text.text = meta['cfr_title_text']
        volume = SubElement(elem, 'volume')
        volume.text = '8'
        date_elem = SubElement(elem, 'date')
        date_elem.text = meta['effective_date']
        orig_date_elem = SubElement(elem, 'originalDate')
        orig_date_elem.text = orig_date
        title_elem = SubElement(elem, 'title')
        title_elem.text = meta['statutory_name']

        return elem

    def preamble(self, reg_number):
        meta = self.layers['meta'][reg_number][0]
        elem = Element('preamble')
        agency = SubElement(elem, 'agency')
        agency.text = 'Bureau of Consumer Financial Protection'
        cfr = SubElement(elem, 'cfr')
        title = SubElement(cfr, 'title')
        title.text = str(meta['cfr_title_number'])
        section = SubElement(cfr, 'section')
        section.text = reg_number
        eff_date = SubElement(elem, 'effectiveDate')
        eff_date.text = meta['effective_date']

        return elem


    @staticmethod
    def toc_to_xml(toc):
        toc_elem = Element('tableOfContents')
        for item in toc:
            index = item['index']
            title = item['title']
            target = '-'.join(index)
            if index[-1].isdigit():
                toc_section = SubElement(toc_elem, 'tocSecEntry', target=target)
                toc_secnum = SubElement(toc_section, 'sectionNum')
                toc_secnum.text = str(index[-1])
                toc_secsubj = SubElement(toc_section, 'sectionSubject')
                toc_secsubj.text = title
            else:
                toc_appentry = SubElement(toc_elem, 'tocAppEntry', target=target)
                toc_appletter = SubElement(toc_appentry, 'appendixLetter')
                toc_appsubj = SubElement(toc_appentry, 'appendixSubject')
                toc_appletter.text = index[-1]
                toc_appsubj.text = title
        return toc_elem

    def to_xml(self, root):
        if root.label[-1] == 'Subpart':
            elem = Element('subpart')
            if root.node_type != "emptypart":
                sub_elem = SubElement(elem, 'title')
                sub_elem.text = root.title
            toc = XMLWriteContent.toc_to_xml(self.layers['toc'][root.label_id()])
            elem.append(toc)
            content = SubElement(elem, 'content')
            for child in root.children:
                sub_elem = self.to_xml(child)
                content.append(sub_elem)
        elif root.label[-1].isdigit() and len(root.label) == 2:
            elem = Element('section', sectionNum=root.label[-1], label=root.label_id())
            subject = SubElement(elem, 'subject')
            subject.text = root.title
            if root.text.strip() != '' and len(root.children) == 0:
                label = root.label_id() + '-a'
                paragraph = SubElement(elem, 'paragraph', marker='', label=label)
                par_content = SubElement(paragraph, 'content')
                par_content.text = root.text.strip()
        elif len(root.label) == 1:
            reg_string = '<regulation xmlns="eregs" ' \
                         'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' \
                         'xsi:schemaLocation="eregs ../../eregs.xsd"></regulation>'
            elem = fromstring(reg_string)
            title = root.title
            fdsys = self.fdsys(root.label_id())
            elem.append(fdsys)
            preamble = self.preamble(root.label_id())
            elem.append(preamble)
            part_num = root.label_id()
            part = SubElement(elem, 'part', partNumber=part_num)
            toc = XMLWriteContent.toc_to_xml(self.layers['toc'][part_num])
            part.append(toc)
            content = SubElement(part, 'content')
            for child in root.children:
                sub_elem = self.to_xml(child)
                content.append(sub_elem)
        elif root.node_type == 'appendix' and len(root.label) == 2:
            elem = Element('appendix', label=root.label_id(), appendixLetter=root.label[-1])
            title = SubElement(elem, 'appendixTitle')
            title.text = root.title
            toc = XMLWriteContent.toc_to_xml(self.layers['toc'][root.label_id()])
            elem.append(toc)
        elif root.node_type == 'appendix' and len(root.label) == 3:
            elem = Element('appendixSection', appendixSecNum=str(self.appendix_sections),
                           label=root.label_id())
            subject = SubElement(elem, 'subject')
            subject.text = root.title
            self.appendix_sections += 1
        else:
            elem = Element('paragraph', label=root.label_id(), marker=root.label[-1])
            title = SubElement(elem, 'title')
            if root.title:
                title.text = root.title
            text = self.apply_layers(root)
            content = fromstring('<content>' + text + '</content>')
            elem.append(content)

        if len(root.label) > 1 and root.label[-1] != 'Subpart':
            # the part is a special case
            for child in root.children:
                sub_elem = self.to_xml(child)
                elem.append(sub_elem)
        return elem

    def apply_layers(self, node):
        text = node.text
        replacement_hashes = {}
        all_offsets = []
        all_replacements = []
        for ident, layer in self.layers.items():
            if node.label_id() in layer:
                replacements = layer[node.label_id()]
                if ident == 'terms':
                    offsets, repls = XMLWriteContent.apply_terms(text, replacements)
                elif ident == 'paragraph-markers':
                    offsets, repls = XMLWriteContent.apply_paragraph_markers(text, replacements)
                elif ident == 'internal-citations':
                    offsets, repls = XMLWriteContent.apply_internal_citations(text, replacements)
                elif ident == 'definitions':
                    offsets, repls = XMLWriteContent.apply_definitions(text, replacements)
                elif ident == 'external-citations':
                    offsets, repls = XMLWriteContent.apply_external_citations(text, replacements)

                all_offsets.extend(offsets)
                all_replacements.extend(repls)

        if len(all_offsets) > 0 and len(all_replacements) > 0:

            offsets_and_repls = zip(all_offsets, all_replacements)
            offsets_and_repls = sorted(offsets_and_repls, key=lambda x: x[0][0])
            all_offsets, all_replacements = zip(*offsets_and_repls)

            text = interpolate_string(text, all_offsets, all_replacements).strip()

        return text

class Client:
    """A Client for writing regulation(s) and meta data."""

    def __init__(self, writer_type=None):
        if writer_type is None:
            if settings.API_BASE:
                self.writer_class = APIWriteContent
            elif getattr(settings, 'GIT_OUTPUT_DIR', ''):
                self.writer_class = GitWriteContent
            else:
                self.writer_class = FSWriteContent
        else:
            if writer_type == 'API':
                self.writer_class = APIWriteContent
            elif writer_type == 'git':
                self.writer_class = GitWriteContent
            elif writer_type == 'XML':
                self.writer_class = XMLWriteContent
            elif writer_type == 'file':
                self.writer_class = FSWriteContent
            else:
                raise ValueError('Unknown writer type specified!')

    def reg_xml(self, label, doc_number, layers=None):
        return self.writer_class("regulation/{}/{}.xml".format(label, doc_number), layers=layers)

    def regulation(self, label, doc_number):
        return self.writer_class("regulation/%s/%s" % (label, doc_number))

    def layer(self, layer_name, label, doc_number):
        return self.writer_class(
            "layer/%s/%s/%s" % (layer_name, label, doc_number))

    def notice(self, doc_number):
        return self.writer_class("notice/%s" % doc_number)

    def diff(self, label, old_version, new_version):
        return self.writer_class("diff/%s/%s/%s" % (label, old_version,
                                                    new_version))

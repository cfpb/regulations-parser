# -*- coding: utf-8 -*-

import os
import os.path
import shutil
import hashlib
import re

from git import Repo
from git.exc import InvalidGitRepositoryError

from lxml.etree import Element, SubElement
from lxml.etree import tostring, fromstring

import requests

from regparser.tree.struct import Node, NodeEncoder, find
from regparser.notice.encoder import AmendmentEncoder
from regparser.tree.xml_parser.reg_text import get_markers

from utils import set_of_random_letters, interpolate_string, ucase_letters

import settings
import logging

class AmendmentNodeEncoder(AmendmentEncoder, NodeEncoder):
    pass


class FSWriteContent:
    """This writer places the contents in the file system """

    def __init__(self, path, doc_number, layers=None, notices=None):
        self.path = path

    def write(self, python_obj, **kwargs):
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
    def __init__(self, path, doc_number, layers=None, notices=None):
        self.path = path

    def write(self, python_obj, **kwargs):
        """Write the object (as json) to the API"""
        requests.post(
            settings.API_BASE + self.path,
            data=AmendmentNodeEncoder().encode(python_obj),
            headers={'content-type': 'application/json'})


class GitWriteContent:
    """This writer places the content in a git repo on the file system"""
    def __init__(self, path, doc_number, layers=None, notices=None):
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

    def write(self, python_object, **kwargs):
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

    def __init__(self, path, doc_number, layers=None, notices=[]):
        self.path = path
        if not self.path.endswith('.xml'):
            self.path = path + '.xml'
        self.doc_number = doc_number
        self.layers = layers
        self.notices = notices
        self.notice = next((n  for n in notices 
                            if n['document_number'] == doc_number), None)
        self.appendix_sections = 1 # need to track these manually
        self.caps = [chr(i) for i in range(65, 65 + 26)]

    def write(self, python_object, **kwargs):
        """ Write the given python object based on its type. Node
            objects are handled as regulation trees, dicts as notices. """
        if isinstance(python_object, Node):
            self.write_regulation(python_object)

        if isinstance(python_object, dict):
            self.write_notice(python_object, **kwargs)

    def write_regulation(self, reg_tree):
        """ Write a regulation tree. """
        self.layers['definitions'] = self.extract_definitions()

        full_path = os.path.join(settings.OUTPUT_DIR, self.path)
        dir_path = os.path.dirname(full_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        xml_tree = self.to_xml(reg_tree)
        xml_string = tostring(xml_tree, pretty_print=True,
                xml_declaration=True, encoding='UTF-8')

        with open(full_path, 'w') as f:
            f.write(xml_string)

    def write_notice(self, notice, changes={}, reg_tree=None):
        """ Write a notice. """
        if reg_tree is None:
            raise RuntimeError("to write notices to XML, both a "
                               "changeset and a reg tree are required.")

        full_path = os.path.join(settings.OUTPUT_DIR, self.path)
        dir_path = os.path.dirname(full_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
        # Create a notice root element
        notice_string = '<notice xmlns="eregs" ' \
                     'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' \
                     'xsi:schemaLocation="eregs ../../eregs.xsd"></notice>'
        notice_elm = fromstring(notice_string)

        # Get the preamble
        preamble_elm = self.preamble(reg_tree.label_id())
        notice_elm.append(preamble_elm)

        # Because analysis kept in-line in RegML, and because the
        # diffing functionality that generated our `changes` doesn't
        # take analysis into account, we need to do so here. Analyzed
        # labels are included as "modified" in the changes dict.
        for label in self.layers['analyses']:
            if label not in changes:
                changes[label] = {'op': 'modified'}

        # Get the changeset
        changeset_elm = Element('changeset')
        for label, change in changes.items():
            # For each change, generate a change element with the label
            # and operation as attributes.
            change_elm = SubElement(changeset_elm, 'change')
            change_elm.set('operation', change['op'])
            change_elm.set('label', label)

            # If the change is added/modified, we also need to include
            # the added/modified node.
            if change['op'] in ('added', 'modified'):
                # Lookup the new label in the regulation tree
                changed_node = find(reg_tree, label)

                # Append it to as XML to the change element
                content_elm = self.to_xml(changed_node)
                change_elm.append(content_elm)

        notice_elm.append(changeset_elm)

        xml_string = tostring(notice_elm, pretty_print=True,
                xml_declaration=True, encoding='UTF-8')

        # Write the file
        with open(full_path, 'w') as f:
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
                a = repl_target.encode('utf-8')
                b = replacement.encode('utf-8')
                replacement = '<ref target="{}" reftype="term">'.format(a) + b + '</ref>'
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
                replacement_text = '<ref target="{}" reftype="internal">'.format(citation_target) + \
                                   ref_text.encode('utf-8') + '</ref>'
                replacement_offsets.append(offset)
                replacement_texts.append(replacement_text)

        return replacement_offsets, replacement_texts

    @staticmethod
    def apply_external_citations(text, replacements):
        replacement_texts = []
        replacement_offsets = []
        for repl in replacements:
            citation = map(str, repl['citation'])
            citation_type = repl['citation_type']
            offsets = repl['offsets']
            for offset in offsets:
                ref_text = text[offset[0]:offset[1]]
                # we need to form a URL for the external citation based on the citation type
                # I don't know how to do that yet so the target is just a placeholder
                target_url = '{}:{}'.format(citation_type, '-'.join(citation))
                replacement_text = '<ref target="{}" reftype="external">'.format(target_url) + \
                                   ref_text.encode('utf-8') + '</ref>'
                replacement_texts.append(replacement_text)
                replacement_offsets.append(offset)

        return replacement_offsets, replacement_texts

    @staticmethod
    def apply_definitions(text, replacement):
        offset = replacement['offset']
        term = replacement['term']
        hash_value = hashlib.sha1(term).hexdigest()
        replacement_text = text[offset[0]:offset[1]]
        replacement_text = '<def term="{}" id="{}">'.format(term, hash_value) + \
                           replacement_text.encode('utf-8') + '</def>'

        return [offset], [replacement_text]

    @staticmethod
    def apply_graphics(graphics_layer):
        graphics_elements = []
        # graphics is a special layer because it's not inlined
        for graphic in graphics_layer:
            graphic_elem = Element('graphic')
            alt_text_elem = SubElement(graphic_elem, 'altText')
            text_elem = SubElement(graphic_elem, 'text')
            url_elem = SubElement(graphic_elem, 'url')

            alt_text_elem.text = graphic['alt']
            text_elem.text = graphic['text']
            url_elem.text = graphic['url']
            if 'thumb_url' in graphic:
                thumb_url_elem = SubElement(graphic_elem, 'thumbUrl')
                thumb_url_elem.text = graphic['thumb_url']

            graphics_elements.append(graphic_elem)

        return graphics_elements

    @staticmethod
    def apply_keyterms(text, replacements):
        pass

    @staticmethod
    def apply_formatting(replacements):
        # format_elements = []
        replacement_texts = []
        replacement_offsets = []
        for repl in replacements:
            if 'dash_data' in repl:
                text = '<dash>' + repl['dash_data']['text'] + '</dash>'
                offset = repl['locations'][0]
                replacement_offsets.append([offset, offset + len(text)])
                replacement_texts.append(text)
            elif 'table_data' in repl:
                text = '<table><header>'
                table_data = repl['table_data']
                header = table_data['header']
                if len(header) > 0:
                    for header_row in header:
                        text += '<columnHeaderRow>'
                        for col in header_row:
                            text += '<column colspan="{}" rowspan="{}">'.format(col['colspan'], col['rowspan'])
                            text += col['text'] + '</column>'
                        text += '</columnHeaderRow>'
                text += '</header>'
                rows = table_data['rows']
                for row in rows:
                    text += '<row>'
                    for item in row:
                        text += '<cell>' + item + '</cell>'
                    text += '</row>'
                text += '</table>'

                offset = repl['locations'][0]
                replacement_offsets.append([offset, offset + len(text)])
                replacement_texts.append(text)

        return replacement_offsets, replacement_texts

    def build_analysis(self, analysis_ref):
        """ Build and return an analysis element for the given analysis
            reference. """
        # We'll need to lookup footnotes in analysis paragraphs in
        # notice['footnotes']. This function does that.
        def resolve_footnotes(text, f_refs):
            annotated_text = ''
            position = 0
            for ref in f_refs:
                ref_offset = ref['offset']
                ref_number = ref['reference']

                # As above, let this KeyError fall through. If the
                # footnote can't be found, we've got bigger
                # problems.
                footnote = analysis_notice['footnotes'][ref_number]
                
                # Create the footnote elm with the text and ref
                # number
                footnote_elm = Element('footnote')
                footnote_elm.set('ref', ref_number)
                footnote_elm.text = footnote
                
                # Add the text to the offset plus the footnote to
                # the annotated string.
                annotated_text += text[position:ref_offset] + \
                        tostring(footnote_elm)

                # Advance our position
                position = ref_offset

            # Add the remainder of the texf
            annotated_text += text[position:]
            return annotated_text

        # Each analysis section will be need to be constructed the
        # same way. So here's a recursive function to do it.
        def analysis_section(parent_elm, child):
            # Create the section element
            section_elm = SubElement(parent_elm, 'analysisSection')

            # Add the title element
            title_elm = SubElement(section_elm, 'title')
            title_elm.text = child['title']

            # Add paragraphs
            for paragraph in child['paragraphs']:
                paragraph_number = child['paragraphs'].index(paragraph)
                paragraph_footnotes = [fn 
                        for fn in child['footnote_refs'] 
                            if fn['paragraph'] == paragraph_number]
                text = resolve_footnotes(paragraph, paragraph_footnotes)

                paragraph_elm = fromstring(
                        '<analysisParagraph>' 
                            + text +
                        '</analysisParagraph>')
                section_elm.append(paragraph_elm)

            # Construct an analysis section for any children.
            map(lambda c:  analysis_section(section_elm, c),
                    child['children'])

        # NOTE: We'll let index errors percolate upwards because if 
        # the index doesn't exist, and we can't find the notice 
        # number or analysis within the notice, there's something 
        # wrong with the analyses layer to this point.
        analysis_version = analysis_ref['reference'][0]
        analysis_label = analysis_ref['reference'][1]

        # Look up the notice with the analysis attached
        analysis_notice = [n for n in self.notices 
                    if n['document_number'] == analysis_version][0]

        # Lookup the analysis for this element
        analysis = [a 
                for a in analysis_notice['section_by_section'] 
                    if analysis_label in a['labels']][0]

        # Construct the analysis element and its sections
        analysis_elm = Element('analysis')
        analysis_section(analysis_elm, analysis)

        return analysis_elm

    def add_analyses(self, elm):
        """
        This method is not like the others above.

        Anlayses are added to the end of the element they analyze. Given
        an element, if analysis exists in the analyses layer for that
        label, an analysis element will be created and appended to the
        given element.
        """

        # If there's no analysis for this label, move on.
        label = elm.get('label')
        if label not in self.layers['analyses']:
            return

        # The analyses for this label.
        analyses = self.layers['analyses'][label]

        for analysis_ref in analyses:
            analysis_elm = self.build_analysis(analysis_ref)
            elm.append(analysis_elm)

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
        doc_number_elm = SubElement(elem, 'documentNumber')
        doc_number_elm.text = self.doc_number
        eff_date = SubElement(elem, 'effectiveDate')
        eff_date.text = meta['effective_date']
        fr_url_elm = SubElement(elem, 'federalRegisterURL')
        fr_url_elm.text = self.notice['fr_url']

        return elem

    @staticmethod
    def toc_to_xml(toc):
        toc_elem = Element('tableOfContents')
        for item in toc:
            index = item['index']
            title = item['title']
            target = '-'.join(index)
            if index[-1].isdigit() and not index[1].isalpha():
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

    @staticmethod
    def is_interp_appendix(node):
        caps = [chr(i) for i in range(65, 65 + 26)]
        if node.node_type == 'interp' and \
            node.label[1] in caps:
            pass

    def to_xml(self, root):
        process_content = False

        if 'Subpart' in root.label:
            elem = Element('subpart')
            if root.node_type != "emptypart":
                title = SubElement(elem, 'title')
                title.text = root.title
            if len(root.label) == 3:
                elem.set('subpartLetter', root.label[-1])
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
                label = root.label_id() + '-p1'
                paragraph = SubElement(elem, 'paragraph', marker='', label=label)
                par_content = SubElement(paragraph, 'content')
                par_content.text = root.text.strip()
            elif '[Reserved]' in root.title:
                reserved = SubElement(elem, 'reserved')
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
            # reset the section counter
            self.appendix_sections = 1
            elem = Element('appendix', label=root.label_id(), appendixLetter=root.label[-1])
            title = SubElement(elem, 'appendixTitle')
            title.text = root.title
            if root.label_id() in self.layers['toc']:
                toc = XMLWriteContent.toc_to_xml(self.layers['toc'][root.label_id()])
                elem.append(toc)
            if '[Reserved]' in root.title:
                reserved = SubElement(elem, 'reserved')
        elif root.node_type == 'appendix' and len(root.label) == 3:
            elem = Element('appendixSection', appendixSecNum=str(self.appendix_sections),
                           label=root.label_id())
            subject = SubElement(elem, 'subject')
            subject.text = root.title
            self.appendix_sections += 1
            if root.text.strip() != '' and len(root.children) == 0:
                label = root.label_id() + '-p1'
                paragraph = SubElement(elem, 'paragraph', marker='', label=label)
                par_content = SubElement(paragraph, 'content')
                par_content.text = root.text.strip()
        elif root.node_type == 'interp' and len(root.label) == 2:
            elem = Element('interpretations', label=root.label_id())
            title = SubElement(elem, 'title')
            title.text = root.title
        elif root.node_type == 'interp'and root.label[1] in self.caps and len(root.label) <= 3:
            # import pdb; pdb.set_trace()
            elem = Element('interpAppendix', appendixLetter=root.label[1], label=root.label_id())
            title = SubElement(elem, 'title')
            title.text = root.title
        elif root.node_type == 'interp' and len(root.label) == 3 and \
                (root.label[1].isdigit() or root.label[1] == 'Interp'):
            if root.label[1].isdigit():
                elem = Element('interpSection', sectionNum=str(root.label[1]), label=root.label_id())
            else:
                elem = Element('interpSection', label=root.label_id())
            title = SubElement(elem, 'title')
            title.text = root.title
            if root.title is not None and '[Reserved]' in root.title:
                reserved = SubElement(elem, 'reserved')
        elif root.node_type == 'interp' and len(root.label) >= 3 and root.label[-1] == 'Interp'\
                and root.label[1] in self.caps:
            # this is the case for hyphenated appendices like MS-1 in reg X
            elem = Element('interpAppSection', appendixLetter=root.label[1], label=root.label_id())
            title = SubElement(elem, 'title')
            title.text = root.title
        elif root.node_type == 'interp': # and \
                #((len(root.label) > 3 and root.label[-1] != 'Interp') or \
                # (len(root.label) == 3 and root.label[1] == 'Interp')):
            # fall-through for all other interp nodes, which should be paragraphs
            target = [item for item in root.label if item != 'Interp']
            target = '-'.join(target)
            label = root.label_id()
            elem = Element('interpParagraph', label=label, target=target)
            if root.title:
                title = SubElement(elem, 'title')
                title.text = root.title
            text = self.apply_layers(root)
            if text.startswith('!'):
                text = ''
            content = fromstring('<content>' + text + '</content>')
            # graphics are special since they're not really inlined
            if root.label_id() in self.layers['graphics']:
                graphics = XMLWriteContent.apply_graphics(self.layers['graphics'][root.label_id()])
                for graphic in graphics:
                    content.append(graphic)
            elem.append(content)
        else:
            try:
                marker_item = self.layers['paragraph-markers'][root.label_id()]
                marker = marker_item[0]['text']
            except KeyError:
                marker = ''
            elem = Element('paragraph', label=root.label_id(), marker=marker)
            if root.title:
                title = SubElement(elem, 'title')
                title.text = root.title
            else:
                if root.label_id() in self.layers['keyterms']:
                    # keyterm is not an inline layer
                    keyterm = self.layers['keyterms'][root.label_id()][0]['key_term']
                    title = SubElement(elem, 'title', attrib={'type': 'keyterm'})
                    title.text = keyterm
            text = self.apply_layers(root)
            if text.startswith('!'):
                text = ''
            content = fromstring('<content>' + text + '</content>')

            # graphics are special since they're not really inlined
            if root.label_id() in self.layers['graphics']:
                graphics = XMLWriteContent.apply_graphics(self.layers['graphics'][root.label_id()])
                for graphic in graphics:
                    content.append(graphic)
            elem.append(content)

        if len(root.label) > 1 and ('Subpart' not in root.label):
            # the part is a special case
            for child in root.children:
                sub_elem = self.to_xml(child)
                elem.append(sub_elem)

            # Add any analysis that might exist for this node
            try:
                self.add_analyses(elem)
            except Exception as ex:
                print 'Could not create analyses for {}'.format(root.label)
                
        return elem

    def apply_layers(self, node):
        text = node.text
        replacement_hashes = {}
        all_offsets = []
        all_replacements = []
        # import pdb; pdb.set_trace()
        # print self.layers.items()
        # print node.label_id()
        for ident, layer in self.layers.items():
            if node.label_id() in layer:
                # print 'applying layers'
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
                elif ident == 'formatting':
                    offsets, repls = XMLWriteContent.apply_formatting(replacements)
                #elif ident == 'graphics':
                #    offsets, repls = XMLWriteContent.apply_graphics(text, replacements)
                else:
                    offsets = []
                    repls = []

                all_offsets.extend(offsets)
                all_replacements.extend(repls)

        if len(all_offsets) > 0 and len(all_replacements) > 0:
            offsets_and_repls = zip(all_offsets, all_replacements)
            offsets_and_repls = sorted(offsets_and_repls, key=lambda x: x[0][0])
            all_offsets, all_replacements = zip(*offsets_and_repls)

            # remove the table text
            if re.search('\|*\|', text):
                text = ''

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

    def regulation(self, label, doc_number, layers=[], notices={}):
        return self.writer_class("regulation/{}/{}".format(label,
            doc_number), doc_number, layers=layers, notices=notices)

    def layer(self, layer_name, label, doc_number):
        return self.writer_class(
            "layer/{}/{}/{}".format(layer_name, label, doc_number),
            doc_number)

    def notice(self, label, doc_number, layers=None, notices={}):
        return self.writer_class("notice/{}/{}.xml".format(label,
            doc_number), doc_number, layers=layers, notices=notices)

    def diff(self, label, old_version, new_version):
        return self.writer_class(
            "diff/{}/{}/{}".format(label, old_version, new_version),
            old_version)

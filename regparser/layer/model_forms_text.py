import string

from regparser.layer.key_terms import KeyTerms
from regparser.layer.layer import Layer
from regparser.tree import struct


class ModelFormText(Layer):
    def __init__(self, *args, **kwargs):
        Layer.__init__(self, *args, **kwargs)
        self.model_forms_sections = []
        self.model_forms_nodes = {}

    def is_appendix(self, node):
        """ Return True if this node is part of the Appendix. False otherwise.
        """

        return len(node.label) > 1 and node.label[1] in string.ascii_uppercase

    def is_model_form(self, node):
        """ Return True if this node has Model Clause(s) or Model Form(s) in
        it's title.  False otherwise. """

        if node.title:
            title = node.title.lower()
            return 'model clause' in title or 'model form' in title
        return False

    def is_model_form_child(self, node):
        for mfs in self.model_forms_sections:
            if node.label_id().startswith(mfs):
                return True
        return False

    def pre_process(self):
        # mark the nodes that are part of a model forms section

        def per_node(node):
            if self.is_appendix(node):
                if self.is_model_form(node):
                    self.model_forms_sections.append(node.label_id())
                    self.model_forms_nodes[node.label_id()] = True
                elif self.is_model_form_child(node):
                    self.model_forms_nodes[node.label_id()] = True

        struct.walk(self.tree, per_node)

    def process(self, node):
        label = node.label_id()
        if label in self.model_forms_nodes and self.model_forms_nodes[label]:
            keyterm = KeyTerms.get_keyterm(node)

            if keyterm:
                end = '</E>'
                node_text = node.text[
                    node.text.find(end) + len(end):].split(' ')
            else:
                node_text = KeyTerms.process_node_text(node).split(' ')

            start_of_model_form = node_text[0]
            end_of_model_form = node_text[-1]

            if start_of_model_form and end_of_model_form:
                list_of_ends = [w for w in node_text if w == end_of_model_form]
                location_end = len(list_of_ends) - 1

                layer_el = [{
                    'start_word': start_of_model_form,
                    'start_locations': [0],
                    'end_word': end_of_model_form,
                    'end_locations':[location_end]
                }]
                return layer_el

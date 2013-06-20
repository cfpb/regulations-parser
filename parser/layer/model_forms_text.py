from layer import Layer
from parser.tree import struct
import string

class ModelFormText(Layer):
    
    def __init__(self, tree):
        Layer.__init__(self, tree)
        self.model_forms_sections = []
        self.model_forms_nodes = {}

    def is_appendix(self, node):
        """ Return True if this node is part of the Appendix. False otherwise. """
        return len(node['label']['parts']) > 1 and node['label']['parts'][1] in string.ascii_uppercase

    def is_model_form(self, node):
        """ Return True if this node has Model Clause(s) or Model Form(s) in it's title. 
        False otherwise. """

        if 'title' in node['label']:
            title = node['label']['title'].lower()
            return 'model clause' in title or 'model form' in title
        return False

    def is_model_form_child(self, node):
        for mfs in self.model_forms_sections:
            if node['label']['text'].startswith(mfs):
                return True
        return False

    def pre_process(self):
        #mark the nodes that are part of a model forms section

        def per_node(node):
            if self.is_appendix(node):
                if self.is_model_form(node):
                    self.model_forms_sections.append(node['label']['text'])
                    self.model_forms_nodes[node['label']['text']] = True
                elif self.is_model_form_child(node):
                    self.model_forms_nodes[node['label']['text']] = True
                    
        struct.walk(self.tree, per_node)

    def process(self, node):
        pass

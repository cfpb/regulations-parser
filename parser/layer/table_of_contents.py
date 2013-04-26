from layer import Layer

class TableOfContentsLayer(Layer):

    def check_toc_candidacy(self, node):
        """ To be eligible to contain a table of contents, all of a node's children must 
        have a title element. """

        if 'children' in node:
            for c in node['children']:
                if 'title' not in c['label']:
                    return False
            return True
        else:
            return False
            
    def process(self, node):
        if self.check_toc_candidacy(node):                
            layer_element = []
            for c in node['children']:
                layer_element.append({'index':c['label']['parts'], 'title':c['label']['title']})
            return layer_element
        return None

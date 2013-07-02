from layer import Layer
from regparser.tree.struct import walk
from regparser.utils import flatten

class SectionBySection(Layer):

    def __init__(self, tree, notices):
        Layer.__init__(self, tree)
        self.notices = notices

    def process(self, node):
        """Determine which (if any) section-by-section analyses would apply
        to this node."""
        analyses = []
        def process_sxs(sxs):
            if 'label' in sxs and sxs['label'] == node['label']['text']:
                return sxs

        for notice in self.notices:
            search_results = flatten([walk(sxs, process_sxs) for sxs in 
                    notice['section_by_section']])
            for found in search_results:
                analyses.append({
                    'text': self.concat(found),
                    'reference': (
                        notice['document_number'], found['label']
                    )
                })
        if analyses:
            return analyses

    def concat(self, sxs_node):
        """Given a node in a section-by-section analysis, concatenate all
        paragraphs and sub-sections."""
        result = "\n".join(sxs_node['paragraphs'])
        child_text = []
        for child in sxs_node['children']:
            child_text.append(self.concat(child))

        return "\n\n".join([result] + child_text)

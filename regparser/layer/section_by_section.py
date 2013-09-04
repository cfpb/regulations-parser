from layer import Layer


class SectionBySection(Layer):

    def __init__(self, tree, notices):
        Layer.__init__(self, tree)
        self.notices = notices

    def process(self, node):
        """Determine which (if any) section-by-section analyses would apply
        to this node."""
        analyses = []
        for notice in self.notices:
            search_results = []

            def per_sxs(sxs):
                if ('label' in sxs and sxs['label'] == node.label_id()
                    # Determine if this is non-empty
                    and (sxs['paragraphs']
                         or [c for c in sxs['children'] if not 'label' in c])):
                    search_results.append(sxs)
                for child in sxs['children']:
                    per_sxs(child)

            for sxs in notice['section_by_section']:
                per_sxs(sxs)

            for found in search_results:
                analyses.append((
                    notice['publication_date'], notice['document_number'],
                    found['label']
                ))
        if analyses:
            #   Sort by publication date
            analyses = sorted(analyses)
            #   Don't need publication date now
            analyses = [{'reference': (a[1], a[2])} for a in analyses]
            return analyses

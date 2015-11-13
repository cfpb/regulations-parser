from layer import Layer


class SectionBySection(Layer):
    def process(self, node):
        """Determine which (if any) section-by-section analyses would apply
        to this node."""
        analyses = []
        for notice in self.notices:
            search_results = []

            def per_sxs(sxs):
                if (node.label_id() in sxs.get('labels', [])
                    # Determine if this is non-empty
                    and (sxs['paragraphs']
                         or any(c for c in sxs['children']
                                if 'labels' not in c))):
                    search_results.append(sxs)
                for child in sxs['children']:
                    per_sxs(child)

            for sxs in notice.get('section_by_section', []):
                per_sxs(sxs)

            for found in search_results:
                analyses.append((
                    notice['publication_date'], notice, found))
        if analyses:
            #   Sort by publication date
            analyses = sorted(analyses)
            analyses = [{'reference': (n['document_number'], node.label_id()),
                         'publication_date': pub_date,
                         'fr_volume': n['fr_volume'],
                         'fr_page': sxs['page']}
                        for pub_date, n, sxs in analyses]
            return analyses

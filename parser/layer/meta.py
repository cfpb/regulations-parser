from layer import Layer
import settings

class Meta(Layer):

    def __init__(self, tree, cfr_title, notices):
        Layer.__init__(self, tree)
        self.cfr_title = cfr_title
        self.notices = notices

    def process(self, node):
        """If this is the root element, add some 'meta' information about
        this regulation, including its cfr title, effective date, and any
        configured info"""
        if len(node['label']['parts']) == 1:
            layer = {
                'cfr_title_number': self.cfr_title,
                'cfr_title_text': settings.CFR_TITLES[self.cfr_title]
            }
            if self.notices:
                for dates in [n['dates']['effective'] for n in self.notices 
                        if 'dates' in n and 'effective' in n['dates']]:
                    layer['effective_date'] = dates[-1]
            return [dict(layer.items() + settings.META.items())]

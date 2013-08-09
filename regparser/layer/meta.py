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
        if len(node.label) != 1:
            return

        layer = {
            'cfr_title_number': self.cfr_title,
            'cfr_title_text': settings.CFR_TITLES[self.cfr_title]
        }
        for notice in self.notices:
            if 'dates' in notice and 'effective' in notice['dates']:
                layer['effective_date'] = notice['dates']['effective'][-1]
        return [dict(layer.items() + settings.META.items())]

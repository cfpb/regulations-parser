from layer import Layer
import settings


class Meta(Layer):

    def __init__(self, tree, cfr_title, notices, version):
        Layer.__init__(self, tree)
        self.cfr_title = cfr_title
        self.notices = notices
        self.version = version

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

        last_notice = filter(lambda n: n['document_number'] == self.version,
                             self.notices)
        if last_notice and 'effective_on' in last_notice[0]:
            layer['effective_date'] = last_notice[0]['effective_on']
        return [dict(layer.items() + settings.META.items())]

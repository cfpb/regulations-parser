from layer import Layer
import settings

class Meta(Layer):

    #   All current, US CFR titles
    cfr_titles = [ None,
        "General Provisions",
        "Grants and Agreements",
        "The President",
        "Accounts",
        "Administrative Personnel",
        "Domestic Security",
        "Agriculture",
        "Aliens and Nationality",
        "Animals and Animal Products",
        "Energy",
        "Federal Elections",
        "Banks and Banking",
        "Business Credit and Assistance",
        "Aeronautics and Space",
        "Commerce and Foreign Trade",
        "Commercial Practices",
        "Commodity and Securities Exchanges",
        "Conservation of Power and Water Resources",
        "Customs Duties",
        "Employees' Benefits",
        "Food and Drugs",
        "Foreign Relations",
        "Highways",
        "Housing and Urban Development",
        "Indians",
        "Internal Revenue",
        "Alcohol, Tobacco Products and Firearms",
        "Judicial Administration",
        "Labor",
        "Mineral Resources",
        "Money and Finance: Treasury",
        "National Defense",
        "Navigation and Navigable Waters",
        "Education",
        "Panama Canal [Reserved]",
        "Parks, Forests, and Public Property",
        "Patents, Trademarks, and Copyrights",
        "Pensions, Bonuses, and Veterans' Relief",
        "Postal Service",
        "Protection of Environment",
        "Public Contracts and Property Management",
        "Public Health",
        "Public Lands: Interior",
        "Emergency Management and Assistance",
        "Public Welfare",
        "Shipping",
        "Telecommunication",
        "Federal Acquisition Regulations System",
        "Transportation",
        "Wildlife and Fisheries",
    ]

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
                'cfr_title_text': Meta.cfr_titles[self.cfr_title]
            }
            if self.notices:
                notice = self.notices[-1]
                if 'dates' in notice and 'effective' in notice['dates']:
                    layer['effective_date'] = notice['dates']['effective'][0]

            return [dict(layer.items() + settings.META.items())]

OUTPUT_DIR = ''
API_BASE = ''
META = {}

#   All current, US CFR titles
CFR_TITLES = [
    None,
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

DEFAULT_IMAGE_URL = (
    'https://s3.amazonaws.com/images.federalregister.gov/' +
    '%s/original.gif')

# list of strings: phrases which shouldn't be broken by definition links
IGNORE_DEFINITIONS_IN = {'ALL':[]}

# List of strings: phrases which should be included as definition links
INCLUDE_DEFINITIONS_IN = {'ALL':[]}

# list of modules implementing the __contains__ and __getitem__ methods
OVERRIDES_SOURCES = [
    'regcontent.overrides'
]

# list of fr notice overrides
FR_NOTICE_OVERRIDES = {'ALL': []}

# list of iterable[(xpath, replacement-xml)] modules, which will be loaded
# in regparser.content.Macros
MACROS_SOURCES = [
    'regcontent.macros'
]

# list of modules implementing the __contains__ and __getitem__ methods
# The key is the notice that needs to be modified; it should point to a dict
# which will get merged with the notice['changes'] dict
REGPATCHES_SOURCES = [
    'regcontent.regpatches'
]

# In some cases, it is beneficial to tweak the XML the Federal Register
# provides. This setting specifies file paths to look through for local
# versions of their XML
LOCAL_XML_PATHS = []


# Sometimes appendices provide examples or model forms that include
# labels that we would otherwise recognize as structural to the appendix
# text itself. This specifies those labels to ignore by regulation
# number, appendix, and label.
APPENDIX_IGNORE_SUBHEADER_LABEL = {}


# It is sometimes necessary to specify the paragraph hierarchy manually
# because of missing or unusual markers. This specifies that hierarchy
# by regulation.
PARAGRAPH_HIERARCHY = {'ALL':[]}

# which notices are complete reissuances
REISSUANCES = []

# It may be necessary to override the 'effective_on', 'dates', etc that
# are fetched from the Federal Register initially, before the XML is
# parsed. This is done per-notice.
FR_NOTICE_OVERRIDES = {}

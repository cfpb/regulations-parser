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

# ImageId -> New URL (without placeholder)
IMAGE_OVERRIDES = {}

# list of strings: phrases which shouldn't be broken by definition links
IGNORE_DEFINITIONS_IN = []

OVERRIDES_SOURCES = [
    'regcontent.overrides'
]

# list of iterable[(xpath, replacement-xml)] modules, which will be loaded
# in regparser.content.Macros
MACROS_SOURCES = [
    'regcontent.macros'
]


try:
    from local_settings import *
except ImportError:
    pass

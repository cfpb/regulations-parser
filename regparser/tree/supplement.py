import re
from regparser.search import find_start


def find_supplement_start(text, supplement='I'):
    """Find the start of the supplement (e.g. Supplement I)"""
    supplement = find_start(text, 'Supplement', supplement)
    commentary = find_start(text, 'Official Commentary on', '')
    return supplement or commentary

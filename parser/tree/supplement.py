import re
from parser.tree.struct import label
from parser.search import find_start


def find_supplement_start(text, supplement='I'):
    """Find the start of the supplement (e.g. Supplement I)"""
    return find_start(text, 'Supplement', supplement)

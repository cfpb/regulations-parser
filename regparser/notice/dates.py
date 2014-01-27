from datetime import datetime
import re

from regparser.tree.xml_parser.tree_utils import get_node_text


def parse_date_sentence(sentence):
    """Return the date type + date in this sentence (if one exists)."""
    #   Search for month date, year at the end of the sentence
    sentence = sentence.lower().strip()
    date_re = r".*((january|february|march|april|may|june|july|august"
    date_re += r"|september|october|november|december) \d+, \d+)$"
    match = re.match(date_re, sentence)
    if match:
        date = datetime.strptime(match.group(1), "%B %d, %Y")
        if 'comment' in sentence:
            return ('comments', date.strftime("%Y-%m-%d"))
        if 'effective' in sentence:
            return ('effective', date.strftime("%Y-%m-%d"))
        return ('other', date.strftime('%Y-%m-%d'))


def fetch_dates(xml_tree):
    """Pull out any dates (and their types) from the XML. Not all notices
    have all types of dates, some notices have multiple dates of the same
    type."""
    dates_field = xml_tree.xpath('//EFFDATE/P') or xml_tree.xpath('//DATES/P')
    dates = {}
    for par in dates_field:
        for sentence in get_node_text(par).split('.'):
            result_pair = parse_date_sentence(sentence.replace('\n', ' '))
            if result_pair:
                date_type, date = result_pair
                dates[date_type] = dates.get(date_type, []) + [date]
    if dates:
        return dates

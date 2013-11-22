from datetime import date
from itertools import dropwhile, takewhile

from regparser.grammar.delays import tokenizer as delay_tokenizer
from regparser.grammar.delays import Delayed, EffectiveDate, Notice


def modify_effective_dates(notices):
    """The effective date of notices can be delayed by other notices. We
    make sure to modify such notices as appropriate."""

    #   Sort so that later modifications supersede earlier ones
    notices = sorted(notices, key=lambda n: n['publication_date'])
    #   Look for modifications to effective date
    for notice in notices:
        #   Only final rules can change effective dates
        if notice['meta']['type'] != 'Rule':
            continue
        if not notice['meta']['dates']:
            continue
        for sent in notice['meta']['dates'].split('.'):
            to_change, changed_to = altered_frs(sent)

            #   notices that have changed
            for n in (n for fr in to_change
                      for n in notices if overlaps_with(fr, n)):
                n['effective_on'] = unicode(changed_to)


def overlaps_with(fr, notice):
    """Calculate whether the fr citation is within the provided notice"""
    return (notice['fr_volume'] == fr.volume
            and notice['meta']['start_page'] <= fr.page
            and notice['meta']['end_page'] >= fr.page)


def altered_frs(sent):
    """Tokenize the provided sentence and check if it is a format that
    indicates that some notices have changed. This format is:
    ... "effective date" ... FRNotices ... "delayed" ... (UntilDate)"""
    tokens = [token[0] for token, _, _ in delay_tokenizer.scanString(sent)]
    tokens = list(dropwhile(lambda t: not isinstance(t, EffectiveDate),
                  tokens))
    if not tokens:
        return [], None
    #   Remove the "effective date"
    tokens = tokens[1:]

    frs = list(takewhile(lambda t: not isinstance(t, Delayed), tokens))
    tokens = tokens[len(frs):]
    frs = [t for t in frs if isinstance(t, Notice)]

    if not frs or not tokens:
        return [], None
    #   Remove the "delayed"
    tokens = tokens[1:]

    tokens = [t for t in tokens if isinstance(t, date)]
    changed_to = None
    if tokens:
        changed_to = tokens[-1]
    return frs, changed_to

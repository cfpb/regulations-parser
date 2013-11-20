from datetime import date
import string

from pyparsing import Optional, Suppress, Word

from regparser.grammar import utils


class EffectiveDate:
    pass


class Notice:
    def __init__(self, volume, page):
        self.volume = volume
        self.page = page

    def __repr__(self):
        return 'Notice( volume=%s, page=%s )' % (repr(self.volume),
                                                 repr(self.page))

    def __eq__(self, other):
        return isinstance(other, Notice) and repr(self) == repr(other)


class Delayed:
    pass


effective_date = (
    utils.Marker("effective") + utils.Marker("date")
).setParseAction(lambda: EffectiveDate())


notice_citation = (
    Word(string.digits)
    + utils.Marker('FR')
    + Word(string.digits)
).setParseAction(lambda m: Notice(int(m[0]), int(m[1])))


delayed = utils.Marker("delayed").setParseAction(lambda: Delayed())


def int2Month(m):
    month = date(2000, m, 1)
    month = month.strftime('%B')
    token = utils.Marker(month)
    return token.setParseAction(lambda: m)


months = reduce(lambda l, r: l | r, map(int2Month, range(2, 13)))


date_parser = (
    months
    + Word(string.digits)
    + Suppress(Optional(","))
    + Word(string.digits)
).setParseAction(lambda m: date(int(m[2]), m[0], int(m[1])))


tokenizer = (effective_date | notice_citation | delayed | date_parser)

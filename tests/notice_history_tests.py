from unittest import TestCase

from regparser.notice.history import *


class NoticeHistoryTests(TestCase):

    def test_modify_effective_dates(self):
        outdated = {'document_number': 'outdated',
                    'effective_on': '2001-01-01',
                    'publication_date': '2000-12-12',
                    'fr_volume': 12,
                    'meta': {'start_page': 500,
                             'end_page': 600,
                             'type': 'Rule',
                             'dates': 'Has an effective date of January 1, '
                                      + '2001'}}
        unaltered = {'document_number': 'unaltered',
                     'effective_on': '2001-01-01',
                     'publication_date': '2000-12-20',
                     'fr_volume': 12,
                     'meta': {'start_page': 800,
                              'end_page': 900,
                              'type': 'Rule',
                              'dates': 'Effective date of January 1, 2001'}}
        proposal = {'document_number': 'proposal',
                    'publication_date': '2000-12-21',
                    'fr_volume': 12,
                    'meta': {
                        'start_page': 1100,
                        'end_page': 1200,
                        'type': 'Proposed Rule',
                        'dates': 'We are thinking about delaying the '
                                 + 'effective date of 12 FR 501 to March 3, '
                                 + '2003'}}
        changer = {'document_number': 'changer',
                   'publication_date': '2000-12-31',
                   'effective_on': '2000-12-31',
                   'fr_volume': 12,
                   'meta': {'start_page': 9000,
                            'end_page': 9005,
                            'type': 'Rule',
                            'dates': 'The effective date of 12 FR 501 has ' +
                                     'been delayed until March 3, 2003'}}

        modify_effective_dates([outdated, unaltered, proposal, changer])

        self.assertEqual('2003-03-03', outdated['effective_on'])
        self.assertEqual('2001-01-01', unaltered['effective_on'])
        self.assertFalse('effective_on' in proposal)
        self.assertEqual('2000-12-31', changer['effective_on'])

    def test_overlaps_with(self):
        fr = Notice(10, 225)
        meta = lambda v, s, e: {'fr_volume': v, 'meta': {'start_page': s,
                                                         'end_page': e}}
        self.assertTrue(overlaps_with(fr, meta(10, 220, 230)))
        self.assertTrue(overlaps_with(fr, meta(10, 225, 230)))
        self.assertTrue(overlaps_with(fr, meta(10, 220, 225)))
        self.assertFalse(overlaps_with(fr, meta(11, 220, 230)))
        self.assertFalse(overlaps_with(fr, meta(10, 226, 230)))
        self.assertFalse(overlaps_with(fr, meta(10, 220, 224)))

    def test_altered_frs(self):
        sent = "The effective date of 12 FR 501, 13 FR 999, and (13 FR 764) "
        sent += "has been delayed."
        self.assertEqual(altered_frs(sent),
                         ([Notice(12, 501), Notice(13, 999), Notice(13, 764)],
                          None))
        sent = "In 11 FR 123 we delayed the effective date"
        self.assertEqual(altered_frs(sent), ([], None))
        sent = "The effective date of 9 FR 765 has been delayed until "
        sent += "January 7, 2008; rather I mean March 4 2008"
        self.assertEqual(altered_frs(sent),
                         ([Notice(9, 765)], date(2008, 3, 4)))

    def test_applicable(self):
        head = {'document_number': 'head',
                'effective_on': '2012-05-05',
                'publication_date': '2011-09-09'}
        history = {'document_number': 'history',
                   'effective_on': '2012-01-01',
                   'publication_date': '2011-04-04'}
        prefinal = {'document_number': 'pre_final',
                    'effective_on': '2012-05-05',
                    'publication_date': '2011-08-08'}
        future = {'document_number': 'future',
                  'effective_on': '2012-05-05',
                  'publication_date': '2011-10-10'}
        notices = applicable([history, head, prefinal, future], 'head')
        self.assertEqual([head, history, prefinal], notices)

    def test_applicable_proposal(self):
        """For now, we ignore proposals"""
        head = {'document_number': 'head',
                'effective_on': '2012-05-05',
                'publication_date': '2011-09-09'}
        proposal = {'document_number': 'proposal',
                    'publication_date': '2011-08-18'}
        notices = applicable([head, proposal], 'head')
        self.assertEqual([head], notices)

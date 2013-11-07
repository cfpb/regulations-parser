from unittest import TestCase

from regparser.history.notices import *


class HistoryNoticesTests(TestCase):
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

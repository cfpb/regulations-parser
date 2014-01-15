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

    def test_group_by_eff_date(self):
        n1 = {'publication_date': '2001-01-01', 'effective_on': '2002-02-02'}
        n2 = {'publication_date': '2001-03-01', 'effective_on': '2002-02-02'}
        n3 = {'publication_date': '2002-02-01', 'effective_on': '2003-02-02'}
        n4 = {'publication_date': '2002-01-01', 'effective_on': '2004-02-02'}
        n5 = {'publication_date': '2001-02-01', 'effective_on': '2002-02-02'}
        grouped = group_by_eff_date([n1, n2, n3, n4, n5])
        self.assertEqual(set(['2002-02-02', '2003-02-02', '2004-02-02']),
                         set(grouped.keys()))
        self.assertEqual([n1, n5, n2], grouped['2002-02-02'])
        self.assertEqual([n3], grouped['2003-02-02'])
        self.assertEqual([n4], grouped['2004-02-02'])

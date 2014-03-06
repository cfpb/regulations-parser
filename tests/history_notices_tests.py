from unittest import TestCase

from regparser.history import notices


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
        notes = notices.applicable([history, head, prefinal, future], 'head')
        self.assertEqual([head, history, prefinal], notes)

    def test_applicable_proposal(self):
        """For now, we ignore proposals"""
        head = {'document_number': 'head',
                'effective_on': '2012-05-05',
                'publication_date': '2011-09-09'}
        proposal = {'document_number': 'proposal',
                    'publication_date': '2011-08-18'}
        notes = notices.applicable([head, proposal], 'head')
        self.assertEqual([head], notes)

    def test_group_by_eff_date(self):
        n = lambda pub, eff, num: {'publication_date': pub,
                                   'effective_on': eff,
                                   'document_number': num}
        n1 = n('2001-01-01', '2002-02-02', '1')
        n2 = n('2001-03-01', '2002-02-02', '2')
        n3 = n('2002-02-01', '2003-02-02', '3')
        n4 = n('2002-01-01', '2004-02-02', '4')
        n5 = n('2001-02-01', '2002-02-02', '5')
        grouped = notices.group_by_eff_date([n1, n2, n3, n4, n5])
        self.assertEqual(set(['2002-02-02', '2003-02-02', '2004-02-02']),
                         set(grouped.keys()))
        self.assertEqual([n1, n5, n2], grouped['2002-02-02'])
        self.assertEqual([n3], grouped['2003-02-02'])
        self.assertEqual([n4], grouped['2004-02-02'])

        n1 = n('2001-01-01', '2002-02-02', '1')
        n2 = n('2001-01-01', '2002-02-02', '2')
        grouped = notices.group_by_eff_date([n1, n2])
        self.assertEqual(grouped['2002-02-02'], [n1, n2])
        grouped = notices.group_by_eff_date([n2, n1])
        self.assertEqual(grouped['2002-02-02'], [n1, n2])

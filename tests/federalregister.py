import json
from mock import patch
from regparser.federalregister import *
from unittest import TestCase

class FederalRegisterTest(TestCase):

    @patch('regparser.federalregister.urlopen')
    @patch('regparser.federalregister.build_notice')
    def test_fetch_notices(self, build_note, urlopen):
        urlopen.return_value.read.return_value = json.dumps({
            "results": [{"some": "thing"}, {"another": "thing"}]})

        build_note.return_value = 'NOTICE!'

        notices = fetch_notices(23, 1222)

        self.assertTrue('23' in urlopen.call_args[0][0])
        self.assertTrue('1222' in urlopen.call_args[0][0])

        self.assertEqual(['NOTICE!', 'NOTICE!'], notices)

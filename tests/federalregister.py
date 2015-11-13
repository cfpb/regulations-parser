from unittest import TestCase

from mock import patch

from regparser import federalregister


class FederalRegisterTest(TestCase):

    @patch('regparser.federalregister.requests')
    @patch('regparser.federalregister.build_notice')
    def test_fetch_notices(self, build_note, requests):
        requests.get.return_value.json.return_value = {
            "results": [{"some": "thing"}, {"another": "thing"}]}

        build_note.return_value = ['NOTICE!']

        notices = federalregister.fetch_notices(23, 1222)

        params = requests.get.call_args[1]['params']
        self.assertTrue(23 in params.values())
        self.assertTrue(1222 in params.values())

        self.assertEqual(['NOTICE!', 'NOTICE!'], notices)

from mock import patch
from regparser.federalregister import *
from unittest import TestCase

class FederalRegisterTest(TestCase):

    @patch('regparser.federalregister.urlopen')
    def test_fetch_notice_xml(self, urlopen):
        """We don't actually want to call out to federal register, so we use
        a mock. Unfortunately, the mock is called twice with two very
        different results, so we need to have a complicated return value."""
        show_xml = [False]  # must use a container class
        def read_response():
            if show_xml[0]:
                return "XML String"
            else:
                show_xml[0] = True
                return """
                <script text="javascript">
                    var dev_formats = {"formats":[
                        {"type":"xml","url":"url.xml",
                            "title":"Original full text XML", "name":"XML"},
                        {"type":"mods","url":"other_url/mods.xml",
                            "title":"Government Printing Office metadata",
                            "name":"MODS"},
                        {"type":"json","url":"final",
                            "title":"Normalized attributes and metadata",
                            "name":"JSON"}]};
                </script>"""
        urlopen.return_value.read.side_effect = read_response
        self.assertEqual('XML String', fetch_notice_xml('initial-url'))


    @patch('regparser.federalregister.urlopen')
    def test_fetch_notices(self, urlopen):
        """Fetch Notices combines data from a lot of places, so we will use
        many mocks."""
        with patch('regparser.federalregister.fetch_notice_xml') as fetch_xml:
            with patch('regparser.federalregister.build_notice') as build_note:
                urlopen.return_value.read.return_value = """
                {"results": [{"html_url": "url1"}, {"html_url": "url2"}]}
                """

                fetch_xml.return_value = '<ROOT />'
                build_note.return_value = 'NOTICE!'

                notices = fetch_notices(23, 1222)

                self.assertTrue('23' in urlopen.call_args[0][0])
                self.assertTrue('1222' in urlopen.call_args[0][0])

                self.assertEqual(2, len(fetch_xml.call_args_list))
                self.assertEqual('url1', fetch_xml.call_args_list[0][0][0])
                self.assertEqual('url2', fetch_xml.call_args_list[1][0][0])

                self.assertEqual(['NOTICE!', 'NOTICE!'], notices)

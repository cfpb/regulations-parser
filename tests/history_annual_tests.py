from unittest import TestCase

from mock import Mock, patch
from requests import Response

from regparser.history import annual


class HistoryAnnualVolumeTests(TestCase):
    @patch('regparser.history.annual.requests')
    def test_init(self, requests):
        response = Response()
        response.status_code = 200
        requests.get.return_value = response
        volume = annual.Volume(1010, 12, 4)
        self.assertEqual(True, volume.exists)

        response.status_code = 404
        volume = annual.Volume(1010, 12, 4)
        self.assertEqual(False, volume.exists)

        self.assertTrue('1010' in requests.get.call_args[0][0])
        self.assertTrue('12' in requests.get.call_args[0][0])
        self.assertTrue('4' in requests.get.call_args[0][0])

    @patch('regparser.history.annual.requests')
    def test_should_contain1(self, requests):
        response = Response()
        response.status_code = 200
        response._content = """
        <CFRDOC>
            <AMDDATE>Jan 1, 2001</AMDDATE>
            <PARTS>Part 111 to 222</PARTS>
        </CFRDOC>"""
        response._content_consumed = True
        requests.get.return_value = response

        volume = annual.Volume(2001, 12, 2)
        self.assertFalse(volume.should_contain(1))
        self.assertFalse(volume.should_contain(100))
        self.assertFalse(volume.should_contain(300))
        self.assertFalse(volume.should_contain(250))
        self.assertTrue(volume.should_contain(111))
        self.assertTrue(volume.should_contain(211))
        self.assertTrue(volume.should_contain(222))

        response._content = """
        <CFRDOC>
            <AMDDATE>Jan 1, 2001</AMDDATE>
            <PARTS>Parts 587 to End</PARTS>
        </CFRDOC>"""
        response._content_consumed = True

        volume = annual.Volume(2001, 12, 2)
        self.assertFalse(volume.should_contain(111))
        self.assertFalse(volume.should_contain(586))
        self.assertTrue(volume.should_contain(587))
        self.assertTrue(volume.should_contain(600))
        self.assertTrue(volume.should_contain(999999))

    @patch('regparser.history.annual.requests')
    def test_should_contain2(self, requests):
        pt111 = """
                    <PART>
                        <EAR>Pt. 111</EAR>
                        <HD SOURCE="HED">PART 111-Something</HD>
                        <FIELD>111 Content</FIELD>
                    </PART>
                """
        pt112 = """
                    <PART>
                        <EAR>Pt. 112</EAR>
                        <HD SOURCE="HED">PART 112-Something</HD>
                        <FIELD>112 Content</FIELD>
                    </PART>
                """

        def side_effect(url, stream=False):
            response = Response()
            response.status_code = 200
            response._content_consumed = True
            if 'bulkdata' in url:
                response._content = """
                <CFRDOC>
                    <AMDDATE>Jan 1, 2001</AMDDATE>
                    <PARTS>Part 111 to 222</PARTS>
                    %s
                    %s
                </CFRDOC>""" % (pt111, pt112)
            elif url.endswith('part111.xml'):
                response._content = pt111
            elif url.endswith('part112.xml'):
                response._content = pt112
            else:
                response.status_code = 404
            return response
        requests.get.side_effect = side_effect

        volume = annual.Volume(2001, 12, 2)

        xml = volume.find_part_xml(111)
        self.assertEqual(len(xml.xpath('./EAR')), 1)
        self.assertEqual(xml.xpath('./EAR')[0].text, 'Pt. 111')
        self.assertEqual(len(xml.xpath('./FIELD')), 1)
        self.assertEqual(xml.xpath('./FIELD')[0].text, '111 Content')

        xml = volume.find_part_xml(112)
        self.assertEqual(len(xml.xpath('./EAR')), 1)
        self.assertEqual(xml.xpath('./EAR')[0].text, 'Pt. 112')
        self.assertEqual(len(xml.xpath('./FIELD')), 1)
        self.assertEqual(xml.xpath('./FIELD')[0].text, '112 Content')

        self.assertEqual(volume.find_part_xml(113), None)


class HistoryAnnua(TestCase):
    def test_annual_edition_for(self):
        for title in range(1, 17):
            notice = {'effective_on': '2000-01-01'}
            self.assertEqual(annual.annual_edition_for(title, notice), 2000)

            notice = {'effective_on': '2000-01-02'}
            self.assertEqual(annual.annual_edition_for(title, notice), 2001)
        for title in range(17, 28):
            notice = {'effective_on': '2000-01-01'}
            self.assertEqual(annual.annual_edition_for(title, notice), 2000)

            notice = {'effective_on': '2000-04-01'}
            self.assertEqual(annual.annual_edition_for(title, notice), 2000)

            notice = {'effective_on': '2000-04-02'}
            self.assertEqual(annual.annual_edition_for(title, notice), 2001)
        for title in range(28, 42):
            notice = {'effective_on': '2000-01-01'}
            self.assertEqual(annual.annual_edition_for(title, notice), 2000)

            notice = {'effective_on': '2000-07-01'}
            self.assertEqual(annual.annual_edition_for(title, notice), 2000)

            notice = {'effective_on': '2000-07-02'}
            self.assertEqual(annual.annual_edition_for(title, notice), 2001)
        for title in range(42, 100):
            notice = {'effective_on': '2000-01-01'}
            self.assertEqual(annual.annual_edition_for(title, notice), 2000)

            notice = {'effective_on': '2000-10-01'}
            self.assertEqual(annual.annual_edition_for(title, notice), 2000)

            notice = {'effective_on': '2000-10-02'}
            self.assertEqual(annual.annual_edition_for(title, notice), 2001)

    @patch('regparser.history.annual.Volume')
    def test_find_volume(self, Volume):
        v1 = Mock()
        v1.exists = True
        v1.should_contain.return_value = False

        v2 = Mock()
        v2.exists = True
        v2.should_contain.return_value = True

        v3 = Mock()
        v3.exists = False

        def side_effect(year, title, vol_num):
            if vol_num > 3:
                return v2
            return v1
        Volume.side_effect = side_effect

        self.assertEqual(annual.find_volume(2000, 11, 3), v2)

        def side_effect(year, title, vol_num):
            if vol_num > 3:
                return v3
            return v1
        Volume.side_effect = side_effect
        self.assertEqual(annual.find_volume(2000, 11, 3), None)

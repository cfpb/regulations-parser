from unittest import TestCase

from mock import patch, Mock

from regparser.layer.graphics import Graphics
from regparser.tree.struct import Node
import settings


class LayerGraphicsTest(TestCase):

    def setUp(self):
        self.default_url = settings.DEFAULT_IMAGE_URL

    def tearDown(self):
        settings.DEFAULT_IMAGE_URL = self.default_url

    def test_process(self):
        node = Node("Testing ![ex](ABCD) then some more XXX " +
                    "some more ![222](XXX) followed by ![ex](ABCD) and XXX " +
                    "and ![](NOTEXT)")
        g = Graphics(None)
        with patch('regparser.layer.graphics.requests'):
            result = g.process(node)
        self.assertEqual(3, len(result))
        found = [False, False, False]
        for res in result:
            if (res['text'] == '![ex](ABCD)'
                    and 'ABCD' in res['url']
                    and res['alt'] == 'ex'
                    and res['locations'] == [0, 1]):
                found[0] = True
            elif (res['text'] == '![222](XXX)'
                  and 'XXX' in res['url']
                  and res['alt'] == '222'
                  and res['locations'] == [0]):
                found[1] = True
            elif (res['text'] == '![](NOTEXT)'
                  and 'NOTEXT' in res['url']
                  and res['alt'] == ''
                  and res['locations'] == [0]):
                found[2] = True

        self.assertEqual([True, True, True], found)

    def test_process_format(self):
        node = Node("![A88 Something](ER22MY13.257-1)")
        g = Graphics(None)
        with patch('regparser.layer.graphics.requests'):
            self.assertEqual(1, len(g.process(node)))

    @patch('regparser.layer.graphics.content')
    def test_process_custom_url(self, content):
        settings.DEFAULT_IMAGE_URL = ":::::%s:::::"
        content.ImageOverrides.return_value = {"a": "AAA", "f": "F8"}

        node = Node("![Alt1](img1)   ![Alt2](f)  ![Alt3](a)")
        g = Graphics(None)
        with patch('regparser.layer.graphics.requests'):
            results = g.process(node)
        self.assertEqual(3, len(results))
        found = [False, False, False]
        for result in results:
            if result['alt'] == 'Alt1' and result['url'] == ':::::img1:::::':
                found[0] = True
            elif result['alt'] == 'Alt2' and result['url'] == 'F8':
                found[1] = True
            elif result['alt'] == 'Alt3' and result['url'] == 'AAA':
                found[2] = True
        self.assertEqual([True, True, True], found)

    def test_find_thumb1(self):
        node = Node("![alt1](img1)")
        settings.DEFAULT_IMAGE_URL = "%s.png"
        g = Graphics(None)
        with patch('regparser.layer.graphics.requests') as requests:
            response = Mock()
            requests.head.return_value = response
            requests.codes.not_implemented = 501
            requests.codes.ok = 200
            response.status_code = 200
            results = g.process(node)

        for result in results:
            self.assertEqual(result['thumb_url'], 'img1.thumb.png')

    def test_find_thumb2(self):
        node = Node("![alt2](img2)")
        settings.DEFAULT_IMAGE_URL = "%s.png"
        g = Graphics(None)
        with patch('regparser.layer.graphics.requests') as requests:
            response = Mock()
            requests.head.return_value = response
            response.status_code = 404
            results = g.process(node)

        for result in results:
            self.assertTrue('thumb_url' not in result)

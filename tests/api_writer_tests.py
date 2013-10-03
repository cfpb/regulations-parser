import json
import os
import shutil
import tempfile
from unittest import TestCase

from mock import patch

from regparser.api_writer import *
import settings


class FSWriteContentTest(TestCase):
    def setUp(self):
        settings.OUTPUT_DIR = tempfile.mkdtemp() + '/'

    def tearDown(self):
        shutil.rmtree(settings.OUTPUT_DIR)
        settings.OUTPUT_DIR = ''

    def test_write_new_dir(self):
        writer = FSWriteContent("a/path/to/something")
        writer.write({"testing": ["body", 1, 2]})

        wrote = json.loads(open(settings.OUTPUT_DIR
                                + '/a/path/to/something').read())
        self.assertEqual(wrote, {'testing': ['body', 1, 2]})

    def test_write_existing_dir(self):
        os.mkdir(settings.OUTPUT_DIR + 'existing')
        writer = FSWriteContent("existing/thing")
        writer.write({"testing": ["body", 1, 2]})

        wrote = json.loads(open(settings.OUTPUT_DIR
                                + '/existing/thing').read())
        self.assertEqual(wrote, {'testing': ['body', 1, 2]})

    def test_write_overwrite(self):
        writer = FSWriteContent("replace/it")
        writer.write({"testing": ["body", 1, 2]})

        writer = FSWriteContent("replace/it")
        writer.write({"key": "value"})

        wrote = json.loads(open(settings.OUTPUT_DIR + '/replace/it').read())
        self.assertEqual(wrote, {'key': 'value'})


class APIWriteContentTest(TestCase):

    def setUp(self):
        self.base = settings.API_BASE
        settings.API_BASE = 'http://example.com/'

    def tearDown(self):
        settings.API_BASE = self.base

    @patch('regparser.api_writer.requests')
    def test_write(self, requests):
        writer = APIWriteContent("a/path")
        data = {"testing": ["body", 1, 2]}
        writer.write(data)

        args, kwargs = requests.post.call_args
        self.assertEqual("http://example.com/a/path", args[0])
        self.assertTrue('headers' in kwargs)
        self.assertTrue('content-type' in kwargs['headers'])
        self.assertEqual('application/json',
                         kwargs['headers']['content-type'])
        self.assertTrue('data' in kwargs)
        self.assertEqual(data, json.loads(kwargs['data']))


class ClientTest(TestCase):

    def setUp(self):
        self.base = settings.API_BASE

    def tearDown(self):
        settings.API_BASE = self.base

    def test_regulation(self):
        client = Client()
        reg_writer = client.regulation("lablab", "docdoc")
        self.assertEqual("regulation/lablab/docdoc", reg_writer.path)

    def test_layer(self):
        client = Client()
        reg_writer = client.layer("boblayer", "lablab", "docdoc")
        self.assertEqual("layer/boblayer/lablab/docdoc", reg_writer.path)

    def test_notice(self):
        client = Client()
        reg_writer = client.notice("docdoc")
        self.assertEqual("notice/docdoc", reg_writer.path)

    def test_diff(self):
        client = Client()
        reg_writer = client.diff("lablab", "oldold", "newnew")
        self.assertEqual("diff/lablab/oldold/newnew", reg_writer.path)

    def test_writer_class(self):
        settings.API_BASE = ''
        client = Client()
        self.assertEqual('FSWriteContent', client.writer_class.__name__)

        settings.API_BASE = 'some url'
        client = Client()
        self.assertEqual('APIWriteContent', client.writer_class.__name__)

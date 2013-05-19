import json
import os
from parser.api_writer import *
import settings
import shutil
import tempfile
from unittest import TestCase

class FSWriteContentTest(TestCase):
    def setUp(self):
        settings.OUTPUT_DIR = tempfile.mkdtemp() + '/'

    def tearDown(self):
        shutil.rmtree(settings.OUTPUT_DIR)
        settings.OUTPUT_DIR = ''

    def test_write_new_dir(self):
        writer = FSWriteContent("a/path")
        writer.write({"testing": ["body", 1, 2]})

        wrote = json.loads(open(settings.OUTPUT_DIR + '/a/path').read())
        self.assertEqual(wrote, {'testing': ['body', 1, 2]})

    def test_write_existing_dir(self):
        os.mkdir(settings.OUTPUT_DIR + 'existing')
        writer = FSWriteContent("existing/thing")
        writer.write({"testing": ["body", 1, 2]})

        wrote = json.loads(open(settings.OUTPUT_DIR + '/existing/thing').read())
        self.assertEqual(wrote, {'testing': ['body', 1, 2]})

    def test_write_overwrite(self):
        writer = FSWriteContent("replace/it")
        writer.write({"testing": ["body", 1, 2]})

        writer = FSWriteContent("replace/it")
        writer.write({"key": "value"})

        wrote = json.loads(open(settings.OUTPUT_DIR + '/replace/it').read())
        self.assertEqual(wrote, {'key': 'value'})


class ClientTest(TestCase):

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

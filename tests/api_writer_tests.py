import json
import os
import shutil
import tempfile
from unittest import TestCase

from mock import patch

from regparser.api_writer import (
    APIWriteContent, Client, FSWriteContent, GitWriteContent, Repo)
from regparser.tree.struct import Node
from regparser.notice.diff import Amendment, DesignateAmendment
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

    def test_write_encoding(self):
        writer = FSWriteContent("replace/it")
        writer.write(Node("Content"))

        wrote = json.loads(open(settings.OUTPUT_DIR + '/replace/it').read())
        self.assertEqual(wrote['text'], 'Content')

        writer.write(Amendment("action", "label"))
        wrote = json.loads(open(settings.OUTPUT_DIR + '/replace/it').read())
        self.assertEqual(wrote, ['action', ['label']])

        writer.write(Amendment("action", "label", 'destination'))
        wrote = json.loads(open(settings.OUTPUT_DIR + '/replace/it').read())
        self.assertEqual(wrote, ['action', ['label'], 'destination'])

        writer.write(DesignateAmendment("action", ["label"], 'destination'))
        wrote = json.loads(open(settings.OUTPUT_DIR + '/replace/it').read())
        self.assertEqual(wrote, ['action', [['label']], 'destination'])


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


class GitWriteContentTest(TestCase):
    def setUp(self):
        self.had_output = hasattr(settings, 'GIT_OUTPUT_DIR')
        self.old_output = getattr(settings, 'GIT_OUTPUT_DIR', '')
        settings.GIT_OUTPUT_DIR = tempfile.mkdtemp() + '/'

    def tearDown(self):
        shutil.rmtree(settings.GIT_OUTPUT_DIR)
        if self.had_output:
            settings.GIT_OUTPUT_DIR = self.old_output
        else:
            del(settings.GIT_OUTPUT_DIR)

    def test_write(self):
        """Integration test."""
        p3a = Node('(a) Par a', label=['1111', '3', 'a'])
        p3b = Node('(b) Par b', label=['1111', '3', 'b'])
        p3 = Node('Things like: ', label=['1111', '3'], title='Section 3',
                  children=[p3a, p3b])
        sub = Node('', label=['1111', 'Subpart', 'E'], title='Subpart E',
                   node_type=Node.SUBPART, children=[p3])
        a3a = Node('Appendix A-3(a)', label=['1111', 'A', '3(a)'],
                   title='A-3(a) - Some Title', node_type=Node.APPENDIX)
        app = Node('', label=['1111', 'A'], title='Appendix A',
                   node_type=Node.APPENDIX, children=[a3a])
        i3a1 = Node('1. P1', label=['1111', '3', 'a', 'Interp', '1'],
                    node_type=Node.INTERP)
        i3a = Node('', label=['1111', '3', 'a', 'Interp'],
                   node_type=Node.INTERP, children=[i3a1],
                   title='Paragraph 3(a)')
        i31 = Node('1. Section 3', label=['1111', '3', 'Interp', '1'],
                   node_type=Node.INTERP)
        i3 = Node('', label=['1111', '3', 'Interp'], node_type=Node.INTERP,
                  title='Section 1111.3', children=[i3a, i31])
        i = Node('', label=['1111', 'Interp'], node_type=Node.INTERP,
                 title='Supplement I', children=[i3])
        tree = Node('Root text', label=['1111'], title='Regulation Joe',
                    children=[sub, app, i])

        writer = GitWriteContent("/regulation/1111/v1v1")
        writer.write(tree)

        dir_path = settings.GIT_OUTPUT_DIR + "regulation" + os.path.sep
        dir_path += '1111' + os.path.sep

        self.assertTrue(os.path.exists(dir_path + '.git'))
        dirs, files = [], []
        for dirname, child_dirs, filenames in os.walk(dir_path):
            if ".git" not in dirname:
                dirs.extend(os.path.join(dirname, c) for c in child_dirs
                            if c != '.git')
                files.extend(os.path.join(dirname, f) for f in filenames)
        for path in (('Subpart-E',), ('Subpart-E', '3'),
                     ('Subpart-E', '3', 'a'), ('Subpart-E', '3', 'b'),
                     ('A',), ('A', '3(a)'),
                     ('Interp',), ('Interp', '3-Interp'),
                     ('Interp', '3-Interp', '1'),
                     ('Interp', '3-Interp', 'a-Interp'),
                     ('Interp', '3-Interp', 'a-Interp', '1')):
            path = dir_path + os.path.join(*path)
            self.assertTrue(path in dirs)
            self.assertTrue(path + os.path.sep + 'index.md' in files)

        p3c = p3b
        p3c.text = '(c) Moved!'
        p3c.label = ['1111', '3', 'c']

        writer = GitWriteContent("/regulation/1111/v2v2")
        writer.write(tree)

        dir_path = settings.GIT_OUTPUT_DIR + "regulation" + os.path.sep
        dir_path += '1111' + os.path.sep

        self.assertTrue(os.path.exists(dir_path + '.git'))
        dirs, files = [], []
        for dirname, child_dirs, filenames in os.walk(dir_path):
            if ".git" not in dirname:
                dirs.extend(os.path.join(dirname, c) for c in child_dirs
                            if c != '.git')
                files.extend(os.path.join(dirname, f) for f in filenames)
        for path in (('Subpart-E',), ('Subpart-E', '3'),
                     ('Subpart-E', '3', 'a'), ('Subpart-E', '3', 'c'),
                     ('A',), ('A', '3(a)'),
                     ('Interp',), ('Interp', '3-Interp'),
                     ('Interp', '3-Interp', '1'),
                     ('Interp', '3-Interp', 'a-Interp'),
                     ('Interp', '3-Interp', 'a-Interp', '1')):
            path = dir_path + os.path.join(*path)
            self.assertTrue(path in dirs)
            self.assertTrue(path + os.path.sep + 'index.md' in files)
        self.assertFalse(dir_path + os.path.join('Subpart-E', '3', 'b')
                         in dirs)

        commit = Repo(dir_path).head.commit
        self.assertTrue('v2v2' in commit.message)
        self.assertEqual(1, len(commit.parents))
        commit = commit.parents[0]
        self.assertTrue('v1v1' in commit.message)
        self.assertEqual(1, len(commit.parents))
        commit = commit.parents[0]
        self.assertTrue('1111' in commit.message)
        self.assertEqual(0, len(commit.parents))


class ClientTest(TestCase):

    def setUp(self):
        self.base = settings.API_BASE
        self.had_git_output = hasattr(settings, 'GIT_OUTPUT_DIR')
        self.old_git_output = getattr(settings, 'GIT_OUTPUT_DIR', '')
        settings.GIT_OUTPUT_DIR = ''

    def tearDown(self):
        settings.API_BASE = self.base
        if self.had_git_output:
            settings.GIT_OUTPUT_DIR = self.old_git_output
        else:
            del(settings.GIT_OUTPUT_DIR)

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

        settings.GIT_OUTPUT_DIR = 'some path'
        client = Client()
        self.assertEqual('GitWriteContent', client.writer_class.__name__)
        settings.GIT_OUTPUT_DIR = ''

        settings.API_BASE = 'some url'
        client = Client()
        self.assertEqual('APIWriteContent', client.writer_class.__name__)

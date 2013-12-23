#vim: set encoding=utf-8
from unittest import TestCase
from lxml import etree
from lxml import html

from regparser.tree.node_stack import NodeStack
from regparser.tree.struct import Node
from regparser.tree.xml_parser import appendices, tree_utils


class AppendicesTest(TestCase):
    def test_process_appendix(self):
        """Integration test for appendices"""
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <P>Intro text</P>
            <HD SOURCE="HD1">Header 1</HD>
            <P>Content H1-1</P>
            <P>Content H1-2</P>
            <HD SOURCE="HD2">Subheader</HD>
            <P>Subheader content</P>
            <HD SOURCE="HD1">Header <E T="03">2</E></HD>
            <P>Final <E T="03">Content</E></P>
            <GPH>
                <PRTPAGE P="650" />
                <GID>MYGID</GID>
            </GPH>
            <FP SOURCE="FR-1">A-3 Some header here</FP>
            <P>Content A-3</P>
            <P>A-4 Another header</P>
            <P>Content A-4</P>
        </APPENDIX>
        """
        appendix = appendices.process_appendix(etree.fromstring(xml), 1111)
        self.assertEqual(5, len(appendix.children))
        intro, h1, h2, a3, a4 = appendix.children

        self.assertEqual([], intro.children)
        self.assertEqual("Intro text", intro.text.strip())

        self.assertEqual(3, len(h1.children))
        self.assertEqual('Header 1', h1.title)
        c1, c2, sub = h1.children
        self.assertEqual([], c1.children)
        self.assertEqual('Content H1-1', c1.text.strip())
        self.assertEqual([], c2.children)
        self.assertEqual('Content H1-2', c2.text.strip())

        self.assertEqual(1, len(sub.children))
        self.assertEqual('Subheader', sub.title)
        self.assertEqual('Subheader content', sub.children[0].text.strip())

        self.assertEqual(2, len(h2.children))
        self.assertEqual('Header 2', h2.title)
        self.assertEqual('Final Content', h2.children[0].text.strip())
        self.assertEqual('![](MYGID)', h2.children[1].text.strip())

        self.assertEqual('A-3 Some header here', a3.title)
        self.assertEqual('A-4 Another header', a4.title)

    def test_remove_toc(self):
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <FP>A-1 Awesome</FP>
            <FP>A-2 More Awesome</FP>
            <FP>A-1 Incorrect TOC</FP>
            <P>A-3 The End of Awesome</P>
            <HD>A-1Awesomer</HD>
            <P>Content content</P>
        </APPENDIX>"""
        #   Note that the title isn't identical
        xml = etree.fromstring(xml)
        appendices.remove_toc(xml, 'A')
        self.assertEqual(['EAR', 'HD', 'HD', 'P'], [t.tag for t in xml])

        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <FP>A-1 Awesome</FP>
            <FP>A-2 More Awesome</FP>
            <FP>A-1 Incorrect TOC</FP>
            <P>A-3 The End of Awesome</P>
            <GPH><GID>GIDGID</GID></GPH>
            <HD>A-3Awesomer</HD>
            <P>Content content</P>
        </APPENDIX>"""
        #   Note that the title isn't identical
        xml = etree.fromstring(xml)
        appendices.remove_toc(xml, 'A')
        self.assertEqual(['EAR', 'HD', 'GPH', 'HD', 'P'], [t.tag for t in xml])

        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <FP>A-1 Awesome</FP>
            <P>Good Content here</P>
            <FP>A-2 More Awesome</FP>
            <P>More Content</P>
            <HD>A-11 Crank It Up</HD>
            <P>Content content</P>
        </APPENDIX>"""
        xml = etree.fromstring(xml)
        appendices.remove_toc(xml, 'A')
        self.assertEqual(['EAR', 'HD', 'FP', 'P', 'FP', 'P', 'HD', 'P'],
                         [t.tag for t in xml])

    def test_title_label_pair(self):
        title = u'A-1—Model Clauses'
        self.assertEqual(('1', 2),
                         appendices.title_label_pair(title, 'A', None))

        title = u'Part III—Construction Period'
        self.assertEqual(('III', 2),
                         appendices.title_label_pair(title, 'A', None))

    def test_title_label_pair_parens(self):
        title = u'G-13(A)—Has No parent'
        stack = NodeStack()
        stack.push_last((1, Node(label=['G'], node_type=Node.APPENDIX)))
        #   Stack: G
        self.assertEqual(('13(A)', 2),
                         appendices.title_label_pair(title, 'G', stack))

        title = u'G-13(A)—Has A parent'
        tree_utils.add_to_stack(stack, 2,
                                Node(label=['13'], node_type=Node.APPENDIX))
        #   Stack: G, 13
        self.assertEqual(('A', 3),
                         appendices.title_label_pair(title, 'G', stack))

        title = u'G-13(B)—Has A Sibling'
        tree_utils.add_to_stack(stack, 3,
                                Node(label=['A'], node_type=Node.APPENDIX))
        #   Stack: G, 13, B
        self.assertEqual(('B', 3),
                         appendices.title_label_pair(title, 'G', stack))

        stack.pop()
        stack.pop()
        tree_utils.add_to_stack(stack, 2,
                                Node(label=['13(A)'], node_type=Node.APPENDIX))
        tree_utils.add_to_stack(stack, 3,
                                Node(label=['a'], node_type=Node.APPENDIX))
        #   Stack: G, 13(A), a
        self.assertEqual(('13(B)', 2),
                         appendices.title_label_pair(title, 'G', stack))

        stack.pop()
        stack.pop()
        tree_utils.add_to_stack(stack, 2,
                                Node(label=['12'], node_type=Node.APPENDIX))
        tree_utils.add_to_stack(stack, 3,
                                Node(label=['A'], node_type=Node.APPENDIX,
                                     title='G-13(A)'))
        #   Stack: G, 12, A
        self.assertEqual(('13(B)', 2),
                         appendices.title_label_pair(title, 'G', stack))


class AppendixProcessorTest(TestCase):
    def setUp(self):
        self.ap = appendices.AppendixProcessor()
        self.ap.paragraph_counter = 0
        self.ap.depth = 0
        self.ap.m_stack = NodeStack()

    def result(self):
        return self.ap.m_stack.peek_last()

    def test_paragraph_no_marker(self):
        self.ap.paragraph_no_marker("Paragraph Text")
        lvl, node = self.result()
        self.assertEqual(node.text, 'Paragraph Text')
        self.assertEqual(0, lvl)
        self.assertEqual(node.label, ['p1'])

        #   If a header was before the paragraph, increment the level 1
        tree_utils.add_to_stack(self.ap.m_stack, 0, Node(
            label=['h1'], title='Some section'))
        self.ap.paragraph_no_marker("Paragraph Text")
        lvl, node = self.result()
        self.assertEqual(node.text, 'Paragraph Text')
        self.assertEqual(1, lvl)
        self.assertEqual(node.label, ['p2'])

    def test_paragraph_with_marker(self):
        self.ap.paragraph_with_marker("(a) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(a) A paragraph')
        self.assertEqual(lvl, 1)
        self.assertEqual(node.label, ['a'])

        self.ap.paragraph_with_marker("(b) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(b) A paragraph')
        self.assertEqual(lvl, 1)
        self.assertEqual(node.label, ['b'])

        self.ap.paragraph_with_marker("(1) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(1) A paragraph')
        self.assertEqual(lvl, 2)
        self.assertEqual(node.label, ['1'])

        self.ap.paragraph_with_marker("(2) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(2) A paragraph')
        self.assertEqual(lvl, 2)
        self.assertEqual(node.label, ['2'])

        self.ap.paragraph_with_marker("(c) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(c) A paragraph')
        self.assertEqual(lvl, 1)
        self.assertEqual(node.label, ['c'])

        self.ap.paragraph_no_marker("Some text")
        lvl, node = self.result()
        self.assertEqual(node.text, 'Some text')
        self.assertEqual(lvl, 1)    # Stay on the same level
        self.assertEqual(node.label, ['p1'])

        self.ap.paragraph_with_marker("(d) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(d) A paragraph')
        self.assertEqual(lvl, 1)
        self.assertEqual(node.label, ['d'])

    def test_paragraph_period(self):
        self.ap.paragraph_with_marker("1. A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '1. A paragraph')
        self.assertEqual(lvl, 1)
        self.assertEqual(node.label, ['1'])

        self.ap.paragraph_with_marker("(b) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(b) A paragraph')
        self.assertEqual(lvl, 2)
        self.assertEqual(node.label, ['b'])

        self.ap.paragraph_with_marker("A. A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, 'A. A paragraph')
        self.assertEqual(lvl, 3)
        self.assertEqual(node.label, ['A'])

        self.ap.paragraph_no_marker("code . is here")
        lvl, node = self.result()
        self.assertEqual(node.text, 'code . is here')
        self.assertEqual(lvl, 3)    # Stay on the same level
        self.assertEqual(node.label, ['p1'])

    def test_paragraph_roman(self):
        self.ap.paragraph_with_marker("(1) A paragraph", "(b) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(1) A paragraph')
        self.assertEqual(lvl, 1)
        self.assertEqual(node.label, ['1'])

        self.ap.paragraph_with_marker("(b) A paragraph", "(i) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(b) A paragraph')
        self.assertEqual(lvl, 2)
        self.assertEqual(node.label, ['b'])

        self.ap.paragraph_with_marker("(i) A paragraph", "(ii) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(i) A paragraph')
        self.assertEqual(lvl, 3)
        self.assertEqual(node.label, ['i'])

        self.ap.paragraph_with_marker("(ii) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(ii) A paragraph')
        self.assertEqual(lvl, 3)
        self.assertEqual(node.label, ['ii'])

        self.ap.paragraph_with_marker("(v) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(v) A paragraph')
        self.assertEqual(lvl, 3)
        self.assertEqual(node.label, ['v'])

    def test_split_paragraph_text(self):
        res = self.ap.split_paragraph_text("(a) Paragraph. (1) Next paragraph")
        self.assertEqual(['(a) Paragraph. ', '(1) Next paragraph', ''], res)

        res = self.ap.split_paragraph_text("(a) (Keyterm) (1) Next paragraph")
        self.assertEqual(['(a) (Keyterm) ', '(1) Next paragraph', ''], res)

        res = self.ap.split_paragraph_text("(a) Mentions one (1) comment")
        self.assertEqual(['(a) Mentions one (1) comment', ''], res)

    def test_paragraph_double_depth(self):
        self.ap.paragraph_with_marker("(a) A paragraph", "(1) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(a) A paragraph')
        self.assertEqual(lvl, 1)
        self.assertEqual(node.label, ['a'])

        self.ap.paragraph_with_marker("(1) A paragraph", "(i) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(1) A paragraph')
        self.assertEqual(lvl, 2)
        self.assertEqual(node.label, ['1'])

        self.ap.paragraph_with_marker("(i) A paragraph", "(A) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(i) A paragraph')
        self.assertEqual(lvl, 3)
        self.assertEqual(node.label, ['i'])

        self.ap.paragraph_with_marker("(A) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(A) A paragraph')
        self.assertEqual(lvl, 4)
        self.assertEqual(node.label, ['A'])

    def test_process_part_cap(self):
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <HD SOURCE="HD1">Part I - Stuff</HD>
            <P>A. Content</P>
        </APPENDIX>
        """
        appendix = self.ap.process(etree.fromstring(xml), 1111)
        self.assertEqual(1, len(appendix.children))
        aI = appendix.children[0]

        self.assertEqual(1, len(aI.children))

    def test_process_header_depth(self):
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <HD SOURCE="HD1">Title 1</HD>
            <P>(1) Content 1</P>
            <P>(2) Content 2</P>
            <HD SOURCE="HD1">Title 2</HD>
            <P>A. Content</P>
        </APPENDIX>
        """
        appendix = self.ap.process(etree.fromstring(xml), 1111)
        self.assertEqual(2, len(appendix.children))
        a1, a2 = appendix.children

        self.assertEqual(2, len(a1.children))
        self.assertEqual(1, len(a2.children))

    def test_process_roman(self):
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <HD SOURCE="HD1">Part I - Something</HD>
            <P>(a) Something</P>
            <GPH><GID>Contains (b)(i) - (iv)</GID></GPH>
            <P>(v) Something else</P>
            <P>(vi) Something more</P>
        </APPENDIX>
        """
        appendix = self.ap.process(etree.fromstring(xml), 1111)
        self.assertEqual(1, len(appendix.children))
        aI = appendix.children[0]
        self.assertEqual(2, len(aI.children))
        aIa, aIb = aI.children
        self.assertEqual(2, len(aIb.children))
        aIv, aIvi = aIb.children
        self.assertEqual(['1111', 'A', 'I', 'a'], aIa.label)
        self.assertEqual(['1111', 'A', 'I', 'p1'], aIb.label)
        self.assertEqual(['1111', 'A', 'I', 'p1', 'v'], aIv.label)
        self.assertEqual(['1111', 'A', 'I', 'p1', 'vi'], aIvi.label)

    def test_process_collapsed(self):
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <HD SOURCE="HD1">Part I - Something</HD>
            <P>(a) Something referencing § 999.2(a)(1). (1) Content</P>
            <P>(2) Something else</P>
        </APPENDIX>
        """
        appendix = self.ap.process(etree.fromstring(xml), 1111)
        self.assertEqual(1, len(appendix.children))
        aI = appendix.children[0]
        self.assertEqual(1, len(aI.children))
        aIa = aI.children[0]
        self.assertEqual(2, len(aIa.children))
        aIa1, aIa2 = aIa.children
        self.assertEqual(['1111', 'A', 'I', 'a', '1'], aIa1.label)
        self.assertEqual('(1) Content', aIa1.text)
        self.assertEqual(['1111', 'A', 'I', 'a', '2'], aIa2.label)
        self.assertEqual('(2) Something else', aIa2.text)

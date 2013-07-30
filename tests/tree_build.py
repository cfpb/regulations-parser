#vim: set encoding=utf-8
from unittest import TestCase

from regparser.tree import struct
from regparser.tree.struct import Node
from regparser.tree.build import *

class TreeBuildTest(TestCase):

    def test_find_cfr_part(self):
        text = "Some text here\n"
        text += "This has 201.44 in it. But also 203.33\n"
        text += "But then, 201.33 returns."

        self.assertEqual(201, find_cfr_part(text))

    def test_build_whole_regtree(self):
        """Integration test for the plain-text regulation tree parser"""
        text = "Regulation Q\n"
        text += u"§ 200.1 First section.\n"
        text += "(a) First par\n"
        text += "(b) Second par\n"
        text += u"§ 200.2 Second section.\n"
        text += "Content without sub pars\n"
        text += "Appendix A to Part 200 - Appendix Title\n"
        text += "A-1 Appendix 1\n"
        text += "(a) Appendix par 1\n"
        text += "Supplement I to Part 200 - Official Interpretations\n"
        text += "Section 200.2 Second section\n"
        text += "2(a)(5) First par\n"
        text += "1. Commentary 1\n"
        text += "2. Commentary 2\n"

        n = struct.node
        l = struct.label
        node201 = n("\n", label=l("200-1", ["200", "1"],
            u"§ 200.1 First section."), children=[
            n(u"(a) First par\n", label=l("200-1-a", ["200","1","a"])),
            n(u"(b) Second par\n", label=l("200-1-b", ["200","1","b"]))
        ])
        node202 = n("\nContent without sub pars\n", label=l("200-2", 
            ["200","2"], u"§ 200.2 Second section."))
        nodeA = n("\n", label=l("200-A", ["200","A"], 
            "Appendix A to Part 200 - Appendix Title"), children=[
            n("\n", label=l("200-A-1", ["200","A","1"], "A-1 Appendix 1"),
                children=[n("(a) Appendix par 1\n", 
                    label=l("200-A-1-a", ["200","A","1","a"]))]
            )]
        )
        nodeI = Node(Node.INTERP, '\n', label=['200', 'Interp'], 
            title='Supplement I to Part 200 - Official Interpretations',
            children=[
                Node(Node.INTERP, '\n', label=['200', '2', 'Interp'],
                    title='Section 200.2 Second section'),
                Node(Node.INTERP, '\n', label=['200','2','a','5','Interp'],
                    title='2(a)(5) First par',
                    children=[
                        Node(Node.INTERP, '1. Commentary 1\n',
                            label=['200', '2', 'a', '5', 'Interp', '1']),
                        Node(Node.INTERP, '2. Commentary 2\n',
                            label=['200', '2', 'a', '5', 'Interp', '2'])
                    ]
                )
            ]
        )
        res = build_whole_regtree(text)
        #   Convert to JSON so we can ignore some unicode issues
        enc = struct.NodeEncoder(sort_keys=True)
        self.assertEqual(
            enc.encode(build_whole_regtree(text)), 
            enc.encode(n("\n", label=l("200", ["200"], "Regulation Q"), 
                children=[ node201, node202, nodeA, nodeI ]))
        )

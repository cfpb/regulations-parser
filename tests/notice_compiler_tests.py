# vim: set encoding=utf-8
from unittest import TestCase

from regparser.notice import compiler
from regparser.tree.struct import Node, find


class CompilerTests(TestCase):
    def test_dict_to_node(self):
        dict_node = {
            'text': 'node text',
            'label': ['205', 'A'],
            'node_type': 'appendix'}

        node = compiler.dict_to_node(dict_node)

        self.assertEqual(
            node,
            Node('node text', [], ['205', 'A'], None, 'appendix'))

        dict_node['tagged_text'] = '<E> Tagged </E> text.'

        node = compiler.dict_to_node(dict_node)

        actual_node = Node('node text', [], ['205', 'A'], None, 'appendix')
        actual_node.tagged_text = '<E> Tagged </E> text.'

        created_node = compiler.dict_to_node(dict_node)

        self.assertEqual(actual_node, created_node)
        self.assertEqual(actual_node.tagged_text, created_node.tagged_text)

        dict_node = {
            'text': 'node text'
        }

        node = compiler.dict_to_node(dict_node)
        self.assertEqual(node, dict_node)

    def test_sort_labels(self):
        labels = [
            ['205', '2', 'a', 'i'], ['205', 'Subpart', 'A'], ['205', '2']]

        sorted_labels = compiler.sort_labels(labels)
        self.assertEqual(
            sorted_labels,
            [['205', 'Subpart', 'A'], ['205', '2'], ['205', '2', 'a', 'i']])

    def test_make_root_sortable(self):
        self.assertEqual(
            compiler.make_root_sortable(['205', 'B'], Node.EMPTYPART),
            (0, 'B'))

        self.assertEqual(
            compiler.make_root_sortable(['205', 'Subpart', 'J'], Node.SUBPART),
            (1, 'J'))

        self.assertEqual(
            compiler.make_root_sortable(['205', 'B'], Node.APPENDIX),
            (2, 'B'))

        self.assertEqual(
            compiler.make_root_sortable(['205', 'Interp'], Node.INTERP),
            (3, ))

    def test_add_child(self):
        n1 = Node('n1', label=['205', '1'])
        n2 = Node('n2', label=['205', '2'])
        n4 = Node('n4', label=['205', '4'])

        children = [n1, n2, n4]

        reg_tree = compiler.RegulationTree(None)

        n3 = Node('n3', label=['205', '3'])
        children = reg_tree.add_child(children, n3)

        self.assertEqual(children, [n1, n2, n3, n4])
        for c in children:
            self.assertFalse(hasattr(c, 'sortable'))

    def test_add_child_appendix(self):
        n1 = Node('M1', label=['205', 'M1'], node_type=Node.APPENDIX)
        n2 = Node('M2', label=['205', 'M2'], node_type=Node.APPENDIX)

        children = [n2]
        children = compiler.RegulationTree(None).add_child(children, n1)

        self.assertEqual(children, [n1, n2])
        n3 = Node('M10a', label=['205', 'M(10)(a)'], node_type=Node.APPENDIX)
        n4 = Node('M10b', label=['205', 'M(10)(b)'], node_type=Node.APPENDIX)

        children = compiler.RegulationTree(None).add_child(children, n4)
        self.assertEqual(children, [n1, n2, n4])
        children = compiler.RegulationTree(None).add_child(children, n3)
        self.assertEqual(children, [n1, n2, n3, n4])

        n5 = Node('p20', label=['205', 'p20'], node_type=Node.APPENDIX)
        n6 = Node('p3', label=['205', 'p3'], node_type=Node.APPENDIX)

        children = compiler.RegulationTree(None).add_child(children, n5)
        self.assertEqual(children, [n1, n2, n3, n4, n5])
        children = compiler.RegulationTree(None).add_child(children, n6)
        self.assertEqual(children, [n1, n2, n3, n4, n6, n5])

    def test_add_child_interp(self):
        reg_tree = compiler.RegulationTree(None)
        n1 = Node('n1', label=['205', '1', 'Interp'])
        n5 = Node('n5', label=['205', '5', 'Interp'])
        n9 = Node('n9', label=['205', '9', 'Interp'])
        n10 = Node('n10', label=['205', '10', 'Interp'])

        children = [n1, n5, n10]
        children = reg_tree.add_child(children, n9)
        self.assertEqual(children, [n1, n5, n9, n10])

        n1.label = ['205', '1', 'a', '1', 'i', 'Interp']
        n5.label = ['205', '1', 'a', '1', 'v', 'Interp']
        n9.label = ['205', '1', 'a', '1', 'ix', 'Interp']
        n10.label = ['205', '1', 'a', '1', 'x', 'Interp']
        children = [n1, n5, n10]
        children = reg_tree.add_child(children, n9)
        self.assertEqual(children, [n1, n5, n9, n10])

        n1.label = ['205', '1', 'a', 'Interp', '1', 'i']
        n5.label = ['205', '1', 'a', 'Interp', '1', 'v']
        n9.label = ['205', '1', 'a', 'Interp', '1', 'ix']
        n10.label = ['205', '1', 'a', 'Interp', '1', 'x']
        children = [n1, n5, n10]
        children = reg_tree.add_child(children, n9)
        self.assertEqual(children, [n1, n5, n9, n10])

        n1.label = ['205', '1', 'Interp', '1']
        n5.label = ['205', '1', 'a', 'Interp']
        children = [n1]
        children = reg_tree.add_child(children, n5)
        self.assertEqual(children, [n1, n5])
        children = [n5]
        children = reg_tree.add_child(children, n1)
        self.assertEqual(children, [n1, n5])

    def test_add_child_order(self):
        reg_tree = compiler.RegulationTree(None)
        n1 = Node('n1', label=['205', 'A', '1'])
        n2 = Node('n2', label=['205', 'A', '2'])
        n3 = Node('n3', label=['205', 'A', '3'])
        n4 = Node('n4', label=['205', 'A', '4'])

        children = []
        order = ['205-A-3', '205-A-2', '205-A-1']
        children = reg_tree.add_child(children, n2, order)
        self.assertEqual(children, [n2])
        children = reg_tree.add_child(children, n1, order)
        self.assertEqual(children, [n1, n2])
        children = reg_tree.add_child(children, n3, order)
        self.assertEqual(children, [n3, n2, n1])
        children = reg_tree.add_child(children, n4, order)
        #   Original order is modified as little as possible
        self.assertEqual(children, [n3, n2, n1, n4])

        children = [n1, n2]
        children = reg_tree.add_child(children, n4, order)
        self.assertEqual(children, [n1, n2, n4])

    def tree_with_paragraphs(self):
        n1 = Node('n1', label=['205', '1'])
        n2 = Node('n2', label=['205', '2'])
        n4 = Node('n4', label=['205', '4'])

        n2a = Node('n2a', label=['205', '2', 'a'])
        n2b = Node('n2b', label=['205', '2', 'b'])
        n2.children = [n2a, n2b]

        root = Node('', label=['205'])
        root.children = [n1, n2, n4]
        return root

    def test_replace_node_and_subtree(self):
        n1 = Node('n1', label=['205', '1'])
        n2 = Node('n2', label=['205', '2'])
        n4 = Node('n4', label=['205', '4'])

        n2a = Node('n2a', label=['205', '2', 'a'])
        n2b = Node('n2b', label=['205', '2', 'b'])
        n2.children = [n2a, n2b]

        root = Node('', label=['205'])
        root.children = [n1, n2, n4]

        reg_tree = compiler.RegulationTree(root)

        a2 = Node('a2', label=['205', '2'])
        a2e = Node('a2e', label=['205', '2', 'e'])
        a2f = Node('a2f', label=['205', '2', 'f'])
        a2.children = [a2e, a2f]

        reg_tree.replace_node_and_subtree(a2)

        new_tree = Node('', label=[205])
        new_tree.children = [n1, a2, n4]

        self.assertEqual(new_tree, reg_tree.tree)
        self.assertEqual(None, find(reg_tree.tree, '205-2-a'))

    def test_replace_node_and_substree_in_place(self):
        n1 = Node('n1', label=['205', '1'])
        n2 = Node('n2', label=['205', '2'])
        n3 = Node('n3', label=['205', '3'])
        root = Node(label=['205'], children=[n2, n1, n3])
        reg_tree = compiler.RegulationTree(root)

        n1_new = Node('n1n1', label=['205', '1'])
        reg_tree.replace_node_and_subtree(n1_new)

        self.assertEqual([['205', '2'], ['205', '1'], ['205', '3']],
                         map(lambda n: n.label, reg_tree.tree.children))
        self.assertEqual(['n2', 'n1n1', 'n3'],
                         map(lambda n: n.text, reg_tree.tree.children))

    def test_reserve_add_new(self):
        root = self.tree_with_paragraphs()
        reg_tree = compiler.RegulationTree(root)

        n2ai = Node('[Reserved]', label=['205', '2', 'a', '1'])
        reg_tree.reserve('205-2-a-1', n2ai)
        self.assertNotEqual(reg_tree.tree, root)
        reserved_node = find(reg_tree.tree, '205-2-a-1')
        self.assertEqual(reserved_node.text, '[Reserved]')

    def test_reserve_existing(self):
        root = self.tree_with_paragraphs()
        reg_tree = compiler.RegulationTree(root)

        before_reserve = find(reg_tree.tree, '205-2-a')
        self.assertNotEqual(before_reserve.text, '[Reserved]')

        n2 = Node('[Reserved]', label=['205', '2'])
        reg_tree.reserve('205-2', n2)
        after_reserve = find(reg_tree.tree, '205-2')
        self.assertEqual(after_reserve.text, '[Reserved]')

        reserve_child = find(reg_tree.tree, '205-2-a')
        self.assertEqual(None, reserve_child)

    def test_add_node(self):
        root = self.tree_with_paragraphs()
        reg_tree = compiler.RegulationTree(root)

        n2ai = Node('n2ai', label=['205', '2', 'a', '1'])
        reg_tree.add_node(n2ai)
        self.assertNotEqual(reg_tree.tree, root)

        n2a = find(root, '205-2-a')
        n2a.children = [n2ai]
        self.assertEqual(reg_tree.tree, root)

    def test_add_node_reserved(self):
        root = self.tree_with_paragraphs()
        reserved_node = Node('[Reserved]', label=['205', '2', 'a', '1'])
        n2a = find(root, '205-2-a')
        n2a.children = [reserved_node]

        reg_tree = compiler.RegulationTree(root)

        parent = find(reg_tree.tree, '205-2-a')
        self.assertEqual(len(parent.children), 1)
        new_node = Node('(i) new content', label=['205', '2', 'a', '1'])
        reg_tree.add_node(new_node)

        added_node = find(reg_tree.tree, '205-2-a-1')
        self.assertEqual(added_node.text, '(i) new content')
        self.assertEqual(len(parent.children), 1)

    def test_add_node_appendix(self):
        root = Node(label=['205'],
                    children=[Node(node_type=Node.SUBPART,
                                   label=['205', 'Subpart', 'A'])])
        reg_tree = compiler.RegulationTree(root)

        appendix = Node(node_type=Node.APPENDIX, label=['205', 'A'])
        reg_tree.add_node(appendix)

        self.assertEqual(2, len(reg_tree.tree.children))
        self.assertEqual(['205', 'Subpart', 'A'],
                         reg_tree.tree.children[0].label)
        self.assertEqual(['205', 'A'], reg_tree.tree.children[1].label)

    def test_add_node_reserved_appendix(self):
        reserved_node = Node('', label=['205', 'R'], node_type=Node.APPENDIX,
                             title='Appendix R-[Reserved]')
        root = Node('', label=['205'], children=[reserved_node])
        reg_tree = compiler.RegulationTree(root)

        new_node = Node('', label=['205', 'R'], node_type=Node.APPENDIX,
                        title="Appendix R-Revision'd", children=[
                            Node('R1', label=['205', 'R', '1'],
                                 node_type=Node.APPENDIX),
                            Node('R2', label=['205', 'R', '2'],
                                 node_type=Node.APPENDIX)])
        reg_tree.add_node(new_node)

        added_node = find(reg_tree.tree, '205-R')
        self.assertEqual(2, len(added_node.children))
        self.assertEqual("Appendix R-Revision'd", added_node.title)

    def test_move_interps(self):
        n1 = Node('n1', label=['205', '1', 'Interp'], node_type=Node.INTERP)
        n2 = Node('n2', label=['205', '2', 'Interp'], node_type=Node.INTERP)
        n4 = Node('n4', label=['205', '4', 'Interp'], node_type=Node.INTERP)

        n4c = Node(
            'n4c', label=['205', '4', 'c', 'Interp'],
            node_type=Node.INTERP)

        n4.children = [n4c]

        n2a = Node(
            'n2a', label=['205', '2', 'a', 'Interp'],
            node_type=Node.INTERP)
        n2b = Node(
            'n2b', label=['205', '2', 'b', 'Interp'],
            node_type=Node.INTERP)
        n2a1 = Node(
            '1. First', label=['205', '2', 'a', 'Interp', '1'],
            node_type=Node.INTERP)

        n2a.children = [n2a1]
        n2.children = [n2a, n2b]

        root = Node('', label=['205', 'Interp'], node_type=Node.INTERP)
        root.children = [n1, n2, n4]

        reg_tree = compiler.RegulationTree(root)
        reg_tree.move('205-2-a-Interp-1', ['205', '4', 'c', 'Interp', '5'])

    def test_move_regtext(self):
        n1 = Node('n1', label=['205', '1'])
        n2 = Node('n2', label=['205', '2'])
        n4 = Node('n4', label=['205', '4'])

        n2a = Node('(a) n2a', label=['205', '2', 'a'])
        n2b = Node('(b) n2b', label=['205', '2', 'b'])
        n2.children = [n2a, n2b]

        root = Node('', label=['205'])
        root.children = [n1, n2, n4]

        reg_tree = compiler.RegulationTree(root)
        reg_tree.move('205-2-b', ['205', '4', 'c'])

        moved = find(reg_tree.tree, '205-4-c')
        self.assertNotEqual(None, moved)
        self.assertTrue('(c)' in moved.text)
        self.assertFalse('(b)' in moved.text)

        no_more = find(reg_tree.tree, '204-2-b')
        self.assertEqual(None, no_more)

    def test_add_to_root(self):
        nsa = Node(
            'nsa',
            label=['205', 'Subpart', 'A'],
            node_type=Node.SUBPART)

        nappa = Node(
            'nappa',
            label=['205', 'Appendix', 'C'],
            node_type=Node.APPENDIX)

        root = Node('', label=['205'])
        root.children = [nsa, nappa]

        reg_tree = compiler.RegulationTree(root)

        nappb = Node(
            'nappb',
            label=['205', 'Appendix', 'B'], node_type=Node.APPENDIX)

        reg_tree.add_to_root(nappb)
        root.children = [nsa, nappb, nappa]

        self.assertEqual(reg_tree.tree, root)

    def test_add_section(self):
        nsa = Node(
            'nsa',
            label=['205', 'Subpart', 'A'],
            node_type=Node.SUBPART)

        nappa = Node(
            'nappa',
            label=['205', 'Appendix', 'C'],
            node_type=Node.APPENDIX)

        root = Node('', label=['205'])
        root.children = [nsa, nappa]

        n1 = Node('', label=['205', '1'])

        reg_tree = compiler.RegulationTree(root)
        reg_tree.add_section(n1, ['205', 'Subpart', 'A'])

        nsa.children = [n1]
        self.assertEqual(reg_tree.tree, root)

    def test_replace_node_text(self):
        root = self.tree_with_paragraphs()

        change = {'node': Node(text='new text')}
        reg_tree = compiler.RegulationTree(root)

        reg_tree.replace_node_text('205-2-a', change)
        changed_node = find(reg_tree.tree, '205-2-a')
        self.assertEqual(changed_node.text, 'new text')

    def test_replace_node_title(self):
        root = self.tree_with_paragraphs()

        change = {'node': Node(title='new title')}
        reg_tree = compiler.RegulationTree(root)

        reg_tree.replace_node_title('205-2-a', change)
        changed_node = find(reg_tree.tree, '205-2-a')
        self.assertEqual(changed_node.title, 'new title')

    def test_replace_node_heading(self):
        root = self.tree_with_paragraphs()
        n2a = find(root, '205-2-a')
        n2a.text = 'Previous keyterm. Remainder.'
        reg_tree = compiler.RegulationTree(root)

        change = {'node': Node(text='Replaced.')}
        reg_tree.replace_node_heading('205-2-a', change)

        changed_node = find(reg_tree.tree, '205-2-a')
        self.assertEqual(changed_node.text, 'Replaced. Remainder.')

    def test_get_subparts(self):
        nsa = Node(
            'nsa',
            label=['205', 'Subpart', 'A'], node_type=Node.SUBPART)

        nsb = Node('nsb',
                   label=['205', 'Subpart', 'B'],
                   node_type=Node.SUBPART)

        nappa = Node('nappa',
                     label=['205', 'Appendix', 'C'],
                     node_type=Node.APPENDIX)

        root = Node('', label=['205'])
        root.children = [nsa, nsb, nappa]

        reg_tree = compiler.RegulationTree(root)
        subparts = reg_tree.get_subparts()
        labels = [s.label_id() for s in subparts]

        self.assertEqual(labels, ['205-Subpart-A', '205-Subpart-B'])

    def tree_with_subparts(self):
        nsa = Node('nsa',
                   label=['205', 'Subpart', 'A'],
                   node_type=Node.SUBPART)

        nsb = Node('nsb',
                   label=['205', 'Subpart', 'B'],
                   node_type=Node.SUBPART)

        nappa = Node('nappa',
                     label=['205', 'Appendix', 'C'],
                     node_type=Node.APPENDIX)

        root = Node('', label=['205'])
        root.children = [nsa, nsb, nappa]
        return root

    def test_replace_subpart_section(self):
        """ Replace a section that already exists in a subpart. """

        root = self.tree_with_subparts()
        section = Node('section', label=['205', '3'], node_type=Node.REGTEXT)
        subpart = find(root, '205-Subpart-B')
        subpart.children = [section]

        reg_tree = compiler.RegulationTree(root)

        new_section = Node(
            'new_section', label=['205', '3'], node_type=Node.REGTEXT)
        reg_tree.replace_node_and_subtree(new_section)

        subpart = find(reg_tree.tree, '205-Subpart-B')
        self.assertEqual(len(subpart.children), 1)
        self.assertEqual(subpart.children[0].text, 'new_section')
        self.assertEqual(len(reg_tree.tree.children), 3)
        subpart_a = find(reg_tree.tree, '205-Subpart-A')
        self.assertEqual(len(subpart_a.children), 0)

    def test_get_section_parent(self):
        root = self.tree_with_subparts()
        section = Node('section', label=['205', '3'], node_type=Node.REGTEXT)
        subpart = find(root, '205-Subpart-B')
        subpart.children = [section]

        reg_tree = compiler.RegulationTree(root)
        parent = reg_tree.get_section_parent(section)
        self.assertEqual(parent.label_id(), '205-Subpart-B')

    def test_get_section_parent_no_subpart(self):
        root = self.tree_with_paragraphs()
        reg_tree = compiler.RegulationTree(root)

        parent = reg_tree.get_section_parent(
            Node('', label=['205', '1'], node_type=Node.REGTEXT))
        self.assertEqual(parent.label_id(), '205')

    def test_create_new_subpart(self):
        root = self.tree_with_subparts()

        reg_tree = compiler.RegulationTree(root)
        reg_tree.create_new_subpart(['205', 'Subpart', 'C'])

        subparts = reg_tree.get_subparts()
        labels = [s.label_id() for s in subparts]

        self.assertEqual(
            labels, ['205-Subpart-A', '205-Subpart-B', '205-Subpart-C'])

    def test_get_subpart_for_node(self):
        root = self.tree_with_subparts()
        n1 = Node('n1', label=['205', '1'])
        nsb = find(root, '205-Subpart-B')
        nsb.children = [n1]

        reg_tree = compiler.RegulationTree(root)
        subpart = reg_tree.get_subpart_for_node('205-1')

        self.assertEqual(subpart.label_id(), '205-Subpart-B')

    def test_compile_reg_put_replace_whole_tree(self):
        root = self.tree_with_paragraphs()

        change2a = {
            'action': 'PUT',
            'node': Node(
                text='new text',
                label=['205', '2', 'a'],
                node_type=Node.REGTEXT)}

        change2a1 = {
            'action': 'PUT',
            'node': Node(
                text='2a1 text',
                label=['205', '2', 'a', '1'],
                node_type=Node.REGTEXT)}

        notice_changes = {
            '205-2-a-1': [change2a1],
            '205-2-a': [change2a]
        }

        reg = compiler.compile_regulation(root, notice_changes)

        added_node = find(reg, '205-2-a')
        self.assertEqual(added_node.text, 'new text')

        deeper = find(reg, '205-2-a-1')
        self.assertEqual(deeper.text, '2a1 text')

    def test_compile_reg_put_text_only(self):
        root = self.tree_with_paragraphs()
        change2a = {
            'action': 'PUT',
            'field': '[text]',
            'node': Node(
                text='new text',
                label=['205', '2', 'a'],
                node_type=Node.REGTEXT)}

        notice_changes = {'205-2-a': [change2a]}
        reg = compiler.compile_regulation(root, notice_changes)

        changed_node = find(reg, '205-2-a')
        self.assertEqual(changed_node.text, 'new text')

    def test_compile_reg_keep_root(self):
        root = self.tree_with_paragraphs()
        change2 = {'action': 'KEEP',
                   'node': Node(text='* * *', label=['205', '2'],
                                node_type=Node.REGTEXT)}
        change2a = {'action': 'PUT',
                    'node': Node(text='(a) A Test', label=['205', '2', 'a'],
                                 node_type=Node.REGTEXT)}

        notice_changes = {'205-2': [change2], '205-2-a': [change2a]}
        reg = compiler.compile_regulation(root, notice_changes)

        changed = find(reg, '205-2')
        self.assertEqual(changed.text, 'n2')    # text didn't change
        self.assertEqual(2, len(changed.children))
        changed2a, changed2b = changed.children
        self.assertEqual(['205', '2', 'a'], changed2a.label)
        self.assertEqual('(a) A Test', changed2a.text)
        self.assertEqual([], changed2a.children)

        self.assertEqual(['205', '2', 'b'], changed2b.label)

    def test_compile_reg_keep_child(self):
        root = self.tree_with_paragraphs()
        change2 = {'action': 'PUT',
                   'node': Node(text='n2n2', label=['205', '2'],
                                node_type=Node.REGTEXT)}
        change2a = {'action': 'KEEP',
                    'node': Node(text='(a) * * *', label=['205', '2', 'a'],
                                 node_type=Node.REGTEXT)}
        change2b = {'action': 'PUT',
                    'node': Node(text='(b) A Test', label=['205', '2', 'b'],
                                 node_type=Node.REGTEXT)}

        notice_changes = {'205-2': [change2], '205-2-a': [change2a],
                          '205-2-b': [change2b]}
        reg = compiler.compile_regulation(root, notice_changes)

        changed = find(reg, '205-2')
        self.assertEqual(changed.text, 'n2n2')
        self.assertEqual(2, len(changed.children))
        changed2a, changed2b = changed.children
        self.assertEqual('n2a', changed2a.text)     # text didn't change
        self.assertEqual('(b) A Test', changed2b.text)

    def test_compile_reg_post_no_subpart(self):
        root = self.tree_with_paragraphs()
        change2a1 = {
            'action': 'POST',
            'node': Node(
                text='2a1 text',
                label=['205', '2', 'a', '1'],
                node_type=Node.REGTEXT)}

        notice_changes = {'205-2-a-1': [change2a1]}
        reg = compiler.compile_regulation(root, notice_changes)
        added_node = find(reg, '205-2-a-1')
        self.assertNotEqual(None, added_node)
        self.assertEqual(added_node.text, '2a1 text')

    def test_compile_reg_move_wrong_reg(self):
        """Changes applied to other regulations shouldn't affect the
        regulation we care about, even if that has the same textual prefix"""
        root = self.tree_with_paragraphs()
        notice_changes = {'2055-2-a': [{'action': 'MOVE',
                                       'destination': ['2055', '2', 'b']}]}
        reg = compiler.compile_regulation(root, notice_changes)
        self.assertEqual(find(reg, '205-2-a').text, 'n2a')
        self.assertEqual(find(reg, '205-2-b').text, 'n2b')
        self.assertEqual(find(reg, '2055-2-b'), None)

    def test_compile_add_to_subpart(self):
        root = self.tree_with_subparts()

        change = {
            'action': 'POST',
            'subpart': ['205', 'Subpart', 'B'],
            'node': Node(
                text='2 text',
                label=['205', '2'],
                node_type=Node.REGTEXT)}

        notice_changes = {'205-2': [change]}
        reg = compiler.compile_regulation(root, notice_changes)
        added_node = find(reg, '205-2')
        self.assertNotEqual(None, added_node)
        self.assertEqual(added_node.text, '2 text')

    def test_compile_designate(self):
        root = self.tree_with_subparts()
        change = {
            'action': 'POST',
            'subpart': ['205', 'Subpart', 'B'],
            'node': Node(
                text='2 text',
                label=['205', '2'],
                node_type=Node.REGTEXT)}

        notice_changes = {'205-2': [change]}
        reg = compiler.compile_regulation(root, notice_changes)

        subpart_b = find(reg, '205-Subpart-B')
        self.assertEqual(len(subpart_b.children), 1)

        subpart_a = find(reg, '205-Subpart-A')
        self.assertEqual(len(subpart_a.children), 0)

        change = {
            'action': 'DESIGNATE',
            'destination': ['205', 'Subpart', 'A']}

        notice_changes = {'205-2': [change]}

        new_reg = compiler.compile_regulation(reg, notice_changes)

        self.assertEqual(None, find(new_reg, '205-Subpart-B'))

        subpart_a = find(new_reg, '205-Subpart-A')
        self.assertEqual(len(subpart_a.children), 1)

    def test_delete(self):
        root = self.tree_with_paragraphs()
        reg_tree = compiler.RegulationTree(root)

        self.assertNotEqual(None, find(reg_tree.tree, '205-2-a'))
        reg_tree.delete('205-2-a')
        self.assertEqual(None, find(reg_tree.tree, '205-2-a'))

        # Verify this doesn't cause an error
        reg_tree.delete('205-2-a')

    def test_get_parent(self):
        root = self.tree_with_paragraphs()
        reg_tree = compiler.RegulationTree(root)

        node = find(reg_tree.tree, '205-2-a')
        parent = reg_tree.get_parent(node)
        self.assertEqual(parent.label, ['205', '2'])

    def test_create_empty(self):
        root = self.tree_with_paragraphs()
        reg_tree = compiler.RegulationTree(root)
        reg_tree.create_empty_node('205-4-a')

        node = find(reg_tree.tree, '205-4-a')
        self.assertNotEqual(None, node)
        self.assertEqual(node.label, ['205', '4', 'a'])
        self.assertEqual(node.node_type, Node.REGTEXT)

        node = Node(label=['205', 'M2'], title='Appendix M2',
                    node_type=Node.APPENDIX)
        reg_tree.add_node(node)
        reg_tree.create_empty_node('205-M2-1')
        node = find(reg_tree.tree, '205-M2-1')
        self.assertNotEqual(None, node)
        self.assertEqual(node.label, ['205', 'M2', '1'])
        self.assertEqual(node.node_type, Node.APPENDIX)

        node = Node(label=['205', Node.INTERP_MARK], title='Supplement I',
                    node_type=Node.INTERP)
        reg_tree.add_node(node)
        reg_tree.create_empty_node('205-3-Interp')
        node = find(reg_tree.tree, '205-3-Interp')
        self.assertNotEqual(None, node)
        self.assertEqual(node.label, ['205', '3', Node.INTERP_MARK])
        self.assertEqual(node.node_type, Node.INTERP)

    def test_create_empty_recursive(self):
        root = self.tree_with_paragraphs()
        reg_tree = compiler.RegulationTree(root)
        reg_tree.create_empty_node('205-4-a-2')

        node = find(reg_tree.tree, '205-4')
        self.assertEqual(1, len(node.children))
        node = node.children[0]

        self.assertEqual(['205', '4', 'a'], node.label)
        self.assertEqual(1, len(node.children))
        node = node.children[0]

        self.assertEqual(['205', '4', 'a', '2'], node.label)
        self.assertEqual(0, len(node.children))

    def test_add_node_no_parent(self):
        root = self.tree_with_paragraphs()
        reg_tree = compiler.RegulationTree(root)

        node = Node('', label=['205', '3', 'a'], node_type=Node.REGTEXT)
        reg_tree.add_node(node)

        parent = find(reg_tree.tree, '205-3')
        self.assertNotEqual(None, parent)
        self.assertEqual(parent.text, '')

    def test_add_node_dummy_subpart(self):
        """If the tree consists only of the empty subpart, adding a new
        section should insert into the empty subpart"""
        root = Node(label=['1'])
        empty = Node(label=['1', 'Subpart'], node_type='emptypart')
        n1 = Node('n1', label=['1', '1'])
        n2 = Node('n2', label=['1', '2'])
        empty.children = [n1, n2]
        root.children = [empty]
        reg_tree = compiler.RegulationTree(root)

        node = Node('n3', label=['1', '3'], node_type=Node.REGTEXT)
        reg_tree.add_node(node)

        self.assertEqual(len(reg_tree.tree.children), 1)
        self.assertEqual(len(reg_tree.tree.children[0].children), 3)

    def test_add_node_placeholder(self):
        node = Node(label=['1234', '2', 'b', '1', Node.INTERP_MARK, '1'],
                    text='1. Some Content',
                    node_type=Node.INTERP)
        node = Node(label=['1234', '2', 'b', '1', Node.INTERP_MARK],
                    title='Paragraph 2(b)(1)',
                    node_type=Node.INTERP, children=[node])
        #   This is the placeholder
        node = Node(label=['1234', '2', 'b', Node.INTERP_MARK],
                    node_type=Node.INTERP, children=[node])
        node = Node(label=['1234', '2', Node.INTERP_MARK],
                    node_type=Node.INTERP, children=[node])
        root = Node(label=['1234'],
                    node_type=Node.REGTEXT,
                    children=[Node(label=['1234', Node.INTERP_MARK],
                                   title='Supplement I',
                                   children=[node])])
        reg_tree = compiler.RegulationTree(root)

        node = Node(label=['1234', '2', 'b', Node.INTERP_MARK],
                    title='2(b) Some Header', node_type=Node.INTERP)
        reg_tree.add_node(node)

        i2 = find(reg_tree.tree, '1234-2-Interp')
        self.assertEqual(1, len(i2.children))

        i2b = i2.children[0]
        self.assertEqual('2(b) Some Header', i2b.title)
        self.assertEqual(1, len(i2b.children))

        i2b1 = i2b.children[0]
        self.assertEqual('Paragraph 2(b)(1)', i2b1.title)
        self.assertEqual(1, len(i2b1.children))

        i2b11 = i2b1.children[0]
        self.assertEqual('1. Some Content', i2b11.text)
        self.assertEqual(0, len(i2b11.children))

    def test_add_node_again(self):
        node = Node(label=['1234', '2', 'b', Node.INTERP_MARK],
                    title='Paragraph 2(b)', node_type=Node.INTERP)
        node = Node(label=['1234', '2', Node.INTERP_MARK],
                    title='Section 1234.2', node_type=Node.INTERP,
                    children=[node])
        root = Node(label=['1234'],
                    node_type=Node.REGTEXT,
                    children=[Node(label=['1234', Node.INTERP_MARK],
                                   title='Supplement I',
                                   children=[node])])
        reg_tree = compiler.RegulationTree(root)

        node = Node(label=['1234', '2', 'b', Node.INTERP_MARK],
                    title='Paragraph 2(b)', node_type=Node.INTERP)
        reg_tree.add_node(node)

        i2 = find(reg_tree.tree, '1234-2-Interp')
        self.assertEqual(1, len(i2.children))

    def test_get_parent_label(self):
        node = Node(node_type=Node.REGTEXT)
        node.label = ['205', '3', 'a']
        self.assertEqual(compiler.get_parent_label(node), "205-3")

        node.label = ['205', '3', 'a', '5', 'ii', 'R']
        self.assertEqual(compiler.get_parent_label(node), "205-3-a-5-ii")

        node.node_type = Node.SUBPART
        self.assertEqual(compiler.get_parent_label(node), "205")

        node.node_type = Node.INTERP
        node.label = ['205', '3', 'a', Node.INTERP_MARK, '1', 'i']
        self.assertEqual(compiler.get_parent_label(node), "205-3-a-Interp-1")

        node.label = ['205', '3', 'a', Node.INTERP_MARK, '1']
        self.assertEqual(compiler.get_parent_label(node), "205-3-a-Interp")

        node.label = ['205', '3', 'a', Node.INTERP_MARK]
        self.assertEqual(compiler.get_parent_label(node), "205-3-Interp")

    def test_replace_first_sentence(self):
        text = "First sentence. Second sentence."
        replacement = "Replaced sentence."
        result = compiler.replace_first_sentence(text, replacement)
        self.assertEqual(result, "Replaced sentence. Second sentence.")

        text = "First sentence."
        replacement = "Replaced sentence."
        result = compiler.replace_first_sentence(text, replacement)
        self.assertEqual(result, "Replaced sentence.")

    def test_compile_regulation_delete_move(self):
        prev_tree = self.tree_with_paragraphs()
        changes = {
            '205-2-a': [
                {'action': 'MOVE', 'destination': ['205', '2', 'b']},
                {'action': 'POST', 'node': Node(text='aaa',
                                                label=['205', '2', 'a'],
                                                node_type=Node.REGTEXT)}],
            '205-2-b': [{'action': 'DELETE'}]}

        class SortedKeysDict(object):
            def keys(self):
                return list(sorted(changes.keys()))

            def __getitem__(self, key):
                return changes[key]

            def __contains__(self, key):
                if key in changes:
                    return True
                else:
                    return False

        new_tree = compiler.compile_regulation(prev_tree, SortedKeysDict())

        s1, s2, s4 = new_tree.children
        self.assertEqual(2, len(s2.children))
        s2a, s2b = s2.children
        self.assertEqual("aaa", s2a.text)
        self.assertEqual("n2a", s2b.text)

    def test_is_reserved_node(self):
        n = Node('[Reserved]', label=['205', '4', 'a'])
        self.assertTrue(compiler.is_reserved_node(n))

        n = Node('(i) a real paragraph', label=['205', '6'])
        self.assertFalse(compiler.is_reserved_node(n))

        n = Node('', title='[Reserved]', label=['205', '7', 'a'])
        self.assertTrue(compiler.is_reserved_node(n))

    def test_overwrite_marker(self):
        n = Node(
            '3. Interpretation paragraph text.',
            label=['205', '2', 'a', 'Interp', '3'],
            node_type=Node.INTERP)

        changed = compiler.overwrite_marker(n, '2')
        self.assertTrue('2.' in changed.text)
        self.assertFalse('3.' in changed.text)

    def test_move_to_subpart(self):
        sect5, sect7 = Node(label=['111', '5']), Node(label=['111', '7'])
        sub_a = Node(label=['111', 'Subpart', 'A'], node_type=Node.SUBPART,
                     children=[sect5])
        sub_b = Node(label=['111', 'Subpart', 'B'], node_type=Node.SUBPART,
                     children=[sect7])

        root = Node(children=[sub_a, sub_b], label=['111'])
        tree = compiler.RegulationTree(root)
        tree.move_to_subpart('111-5', sub_b.label)
        sub_b = find(tree.tree, '111-Subpart-B')
        sect5, sect7 = find(tree.tree, '111-5'), find(tree.tree, '111-7')
        self.assertEqual([sub_b], tree.tree.children)
        self.assertEqual([sect5, sect7], sub_b.children)

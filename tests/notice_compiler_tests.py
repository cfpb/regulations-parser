#vim: set encoding=utf-8
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
            compiler.make_root_sortable(['205', 'B'], Node.APPENDIX),
            (1, 'B'))

        self.assertEqual(
            compiler.make_root_sortable(['205', 'Subpart', 'J'], Node.SUBPART),
            (0, 'J'))

        self.assertEqual(
            compiler.make_root_sortable(['205', 'Interp'], Node.INTERP),
            (2, ))

    def test_add_child(self):
        n1 = Node('n1', label=['205', '1'])
        n2 = Node('n2', label=['205', '2'])
        n4 = Node('n4', label=['205', '4'])

        children = [n1, n2, n4]

        reg_tree = compiler.RegulationTree(None)

        n3 = Node('n3', label=['205', '3'])
        reg_tree.add_child(children, n3)

        self.assertEqual(children, [n1, n2, n3, n4])
        for c in children:
            self.assertFalse(hasattr(c, 'sortable'))

    def test_add_child_appendix(self):
        n1 = Node('M1', label=['205', 'M1'])
        n2 = Node('M2', label=['205', 'M2'])

        children = [n2]
        compiler.RegulationTree(None).add_child(children, n1)

        self.assertEqual(children, [n1, n2])

    def test_add_child_interp(self):
        reg_tree = compiler.RegulationTree(None)
        n1 = Node('n1', label=['205', '1', 'Interp'])
        n5 = Node('n5', label=['205', '5', 'Interp'])
        n9 = Node('n9', label=['205', '9', 'Interp'])
        n10 = Node('n10', label=['205', '10', 'Interp'])

        children = [n1, n5, n10]
        reg_tree.add_child(children, n9)
        self.assertEqual(children, [n1, n5, n9, n10])

        n1.label = ['205', '1', 'a', '1', 'i', 'Interp']
        n5.label = ['205', '1', 'a', '1', 'v', 'Interp']
        n9.label = ['205', '1', 'a', '1', 'ix', 'Interp']
        n10.label = ['205', '1', 'a', '1', 'x', 'Interp']
        children = [n1, n5, n10]
        reg_tree.add_child(children, n9)
        self.assertEqual(children, [n1, n5, n9, n10])

        n1.label = ['205', '1', 'a', 'Interp', '1', 'i']
        n5.label = ['205', '1', 'a', 'Interp', '1', 'v']
        n9.label = ['205', '1', 'a', 'Interp', '1', 'ix']
        n10.label = ['205', '1', 'a', 'Interp', '1', 'x']
        children = [n1, n5, n10]
        reg_tree.add_child(children, n9)
        self.assertEqual(children, [n1, n5, n9, n10])

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
        self.assertEqual(children, [n1, n2, n3, n4])

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

    def test_move(self):
        root = self.tree_with_paragraphs()
        reg_tree = compiler.RegulationTree(root)
        reg_tree.move('205-2-a', ['205', '4', 'a'])

        moved = find(reg_tree.tree, '205-4-a')
        self.assertNotEqual(None, moved)
        self.assertEqual(moved.text, 'n2a')
        self.assertEqual(None, find(reg_tree.tree, '205-2-a'))

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

        change = {'node': {'text': 'new text'}}
        reg_tree = compiler.RegulationTree(root)

        reg_tree.replace_node_text('205-2-a', change)
        changed_node = find(reg_tree.tree, '205-2-a')
        self.assertEqual(changed_node.text, 'new text')

    def test_replace_node_title(self):
        root = self.tree_with_paragraphs()

        change = {'node': {'title': 'new title'}}
        reg_tree = compiler.RegulationTree(root)

        reg_tree.replace_node_title('205-2-a', change)
        changed_node = find(reg_tree.tree, '205-2-a')
        self.assertEqual(changed_node.title, 'new title')

    def test_replace_node_heading(self):
        root = self.tree_with_paragraphs()
        n2a = find(root, '205-2-a')
        n2a.text = 'Previous keyterm. Remainder.'
        reg_tree = compiler.RegulationTree(root)

        change = {'node': {'text': 'Replaced.'}}
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
            'node': {
                'text': 'new text',
                'label': ['205', '2', 'a'],
                'node_type': 'regtext'}}

        change2a1 = {
            'action': 'PUT',
            'node': {
                'text': '2a1 text',
                'label': ['205', '2', 'a', '1'],
                'node_type': 'regtext'}}

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
            'node': {
                'text': 'new text',
                'label': ['205', '2', 'a'],
                'node_type': 'regtext'}}

        notice_changes = {'205-2-a': [change2a]}
        reg = compiler.compile_regulation(root, notice_changes)

        changed_node = find(reg, '205-2-a')
        self.assertEqual(changed_node.text, 'new text')

    def test_compile_reg_post_no_subpart(self):
        root = self.tree_with_paragraphs()
        change2a1 = {
            'action': 'POST',
            'node': {
                'text': '2a1 text',
                'label': ['205', '2', 'a', '1'],
                'node_type': 'regtext'}}

        notice_changes = {'205-2-a-1': [change2a1]}
        reg = compiler.compile_regulation(root, notice_changes)
        added_node = find(reg, '205-2-a-1')
        self.assertNotEqual(None, added_node)
        self.assertEqual(added_node.text, '2a1 text')

    def test_compile_reg_move_wrong_reg(self):
        root = self.tree_with_paragraphs()
        notice_changes = {'202-2-a': [{'action': 'MOVE',
                                       'destination': ['202', '2', 'b']}]}
        reg = compiler.compile_regulation(root, notice_changes)
        self.assertEqual(find(reg, '205-2-a').text, 'n2a')

    def test_compile_add_to_subpart(self):
        root = self.tree_with_subparts()

        change = {
            'action': 'POST',
            'subpart': ['205', 'Subpart', 'B'],
            'node': {
                'text': '2 text',
                'label': ['205', '2'],
                'node_type': 'regtext'}}

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
            'node': {
                'text': '2 text',
                'label': ['205', '2'],
                'node_type': 'regtext'}}

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

        subpart_b = find(new_reg, '205-Subpart-B')
        self.assertEqual(len(subpart_b.children), 0)

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

    def test_add_node_no_parent(self):
        root = self.tree_with_paragraphs()
        reg_tree = compiler.RegulationTree(root)

        node = Node('', label=['205', '3', 'a'], node_type=Node.REGTEXT)
        reg_tree.add_node(node)

        parent = find(reg_tree.tree, '205-3')
        self.assertNotEqual(None, parent)
        self.assertEqual(parent.text, '')

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
                {'action': 'POST', 'node': {'text': 'aaa',
                                            'label': ['205', '2', 'a'],
                                            'node_type': Node.REGTEXT}}],
            '205-2-b': [{'action': 'DELETE'}]}

        class SortedKeysDict(object):
            def keys(self):
                return list(sorted(changes.keys()))

            def __getitem__(self, key):
                return changes[key]

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

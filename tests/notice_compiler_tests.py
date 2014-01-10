#vim: set encoding=utf-8
from unittest import TestCase
from regparser.notice import compiler
from regparser.tree.struct import Node, find


class CompilerTests(TestCase):
    def test_dict_to_node(self):
        dict_node = {
            'text': 'node text', 
            'label':['205', 'A'], 
            'node_type':'appendix'}

        node = compiler.dict_to_node(dict_node) 


        self.assertEqual(
            node,
            Node('node text', [], ['205', 'A'], None, 'appendix'))

        dict_node['tagged_text'] = '<E> Tagged </E> text.'

        node = compiler.dict_to_node(dict_node)

        actual_node = Node('node text', [], ['205', 'A'], None, 'appendix')
        actual_node.tagged_text = '<E> Tagged </E> text.'

        self.assertEqual(actual_node, compiler.dict_to_node(dict_node))

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
        a2f= Node('a2f', label=['205', '2', 'f'])
        a2.children = [a2e, a2f]

        reg_tree.replace_node_and_subtree(a2)

        new_tree = Node('', label=[205])
        new_tree.children = [n1, a2, n4]

        self.assertEqual(new_tree, reg_tree.tree)
        self.assertEqual(None, find(reg_tree.tree, '205-2-a'))

    def test_add_node(self):
        root = self.tree_with_paragraphs()
        reg_tree = compiler.RegulationTree(root)

        n2ai = Node('n2ai', label=['205', '2', 'a', '1'])
        reg_tree.add_node(n2ai)
        self.assertNotEqual(reg_tree.tree, root)

        n2a = find(root, '205-2-a')
        n2a.children = [n2ai]
        self.assertEqual(reg_tree.tree, root)

    
    def test_add_to_root(self):
        nsa = Node('nsa', 
                  label=['205', 'Subpart', 'A'], 
                  node_type=Node.SUBPART) 

        nappa = Node('nappa', 
                    label = ['205', 'Appendix', 'C'], 
                    node_type = Node.APPENDIX)

        root = Node('', label=['205'])
        root.children = [nsa, nappa]

        reg_tree = compiler.RegulationTree(root)

        nappb = Node('nappb', 
                    label=['205', 'Appendix', 'B'], node_type=Node.APPENDIX)

        reg_tree.add_to_root(nappb)
        root.children = [nsa, nappb, nappa]

        self.assertEqual(reg_tree.tree, root)

    def test_add_section(self):
        nsa = Node('nsa', 
          label=['205', 'Subpart', 'A'], 
          node_type=Node.SUBPART) 

        nappa = Node('nappa', 
            label=['205', 'Appendix', 'C'], 
            node_type=Node.APPENDIX)

        root = Node('', label = ['205'])
        root.children = [nsa, nappa]

        n1 = Node('', label = ['205', '1'])

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

    def test_get_subparts(self):
        nsa = Node('nsa', 
                   label=['205', 'Subpart', 'A'], 
                   node_type=Node.SUBPART)

        nsb = Node('nsb', 
                   label=['205', 'Subpart', 'B'], 
                   node_type=Node.SUBPART)

        nappa = Node('nappa', 
                     label=['205', 'Appendix', 'C'], 
                     node_type=Node.APPENDIX)

        root = Node('', label = ['205'])
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

        root = Node('', label = ['205'])
        root.children = [nsa, nsb, nappa]
        return root

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

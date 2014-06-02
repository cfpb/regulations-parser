class PriorityStack(object):
    def __init__(self):
        self.m_stack = [[]]

    def pop(self):
        return self.m_stack.pop()

    def peek(self):
        return self.m_stack[-1]

    def push(self, m):
        self.m_stack.append([m])

    def push_last(self, m):
        self.m_stack[-1].append(m)

    def peek_last(self):
        return self.m_stack[-1][-1]

    def peek_level(self, level):
        """Find a whole level of nodes in the stack"""
        for layer in self.m_stack:
            if layer and layer[0][0] == level:
                return [node for _, node in layer]

    def peek_level_last(self, level):
        """Get the last from a level of nodes in the stack"""
        found = self.peek_level(level)
        if found:
            return found[-1]

    def lineage(self):
        """Fetch the last element of each level of priorities. When the
        stack is used to keep track of a tree, this list includes a list of
        'parents', as the last element of each level is the parent being
        processed."""
        if self.m_stack[0]:
            return list(reversed([els[-1][-1] for els in self.m_stack]))
        else:
            return []

    def lineage_with_level(self):
        if self.m_stack[0]:
            return list(reversed([els[-1] for els in self.m_stack]))
        else:
            return []

    def add_to_bottom(self, m):
        self.m_stack = [[m]] + self.m_stack

    def size(self):
        return len(self.m_stack)

    def unwind(self):
        """Combine nodes as needed while walking back up the stack. Intended
        to be overridden, as how to combine elements depends on the element
        type."""
        raise NotImplementedError

    def add(self, node_level, node):
        """ Add a new node with level node_level to the stack. Unwind the stack
        when necessary. """
        last = self.peek()
        element = (node_level, node)

        if len(last) > 0 and node_level > last[0][0]:
            self.push(element)
        elif len(last) > 0 and node_level < last[0][0]:
            while last[0][0] > node_level:
                self.unwind()
                last = self.peek()
            self.push_last(element)
        else:
            self.push_last(element)

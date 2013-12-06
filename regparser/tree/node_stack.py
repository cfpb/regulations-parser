class NodeStack(object):
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

    def add_to_bottom(self, m):
        self.m_stack = [[m]] + self.m_stack

    def size(self):
        return len(self.m_stack)

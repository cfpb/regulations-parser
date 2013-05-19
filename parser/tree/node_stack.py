class MarkerStack():
    def __init__(self):
        self.m_stack = [[]]

    def pop():
        return self.m_stack.pop()

    def peek():
        return self.m_stack[-1]

    def push(m):
        self.m_stack.append(m)

    def push_last(m):
        self.m_stack[-1].append(m)

    def peek_last():
        return self.m_stack[-1][-1]

    def unwind():
        children = self.pop()
        parts_prefix = self.peek_last()[1]['label']['parts']
        children = [prepend_parts(parts_prefix, c[1]) for c in children]
        self.peek_last()[1]['children'] = children

from collections import deque


class Node:
    def __init__(self, value):
        self.value = value
        self.parent = None
        self.children = []

    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def __str__(self):
        parent_value = self.parent.value if self.parent else 'root'
        return f'{parent_value}->{self.value}'


class Tree:
    def __init__(self, root):
        self.root = root

    def bfs(self, func):
        curr_level = [self.root]
        while curr_level:
            for node in curr_level:
                func(node)
            curr_level = [c for n in curr_level for c in n.children]

    @classmethod
    def _preorder(cls, node, func):
        func(node)
        for child in node.children:
            cls._preorder(child, func)

    def dfs_preorder(self, func):
        self._preorder(self.root, func)

    @classmethod
    def _postorder(cls, node, func):
        for child in node.children:
            cls._postorder(child, func)
        func(node)

    def dfs_postorder(self, func):
        self._postorder(self.root, func)


class TreeBuilder:
    def __init__(self, max_children):
        self.root = None
        self.max_children = max_children
        self.queue = deque()

    def insert(self, value):
        new_node = Node(value)
        if self.root is None:
            self.root = new_node
            self.queue.append(self.root)
            return

        while self.queue:
            node = self.queue.popleft()
            if len(node.children) < self.max_children:
                node.add_child(new_node)
                self.queue.appendleft(node)
                return
            else:
                self.queue.extend(node.children)

    def build(self):
        return Tree(self.root)


if __name__ == '__main__':
    builder = TreeBuilder(max_children=3)
    for idx in range(20):
        builder.insert(f'Node-{idx}')
    tree = builder.build()

    print('Breadth-first search')
    print('--------------------')
    tree.bfs(lambda node: print(node))

    print()
    print('Pre-order Depth-first search')
    print('--------------------')
    tree.dfs_preorder(lambda node: print(node))

    print()
    print('Post-order Depth-first search')
    print('--------------------')
    tree.dfs_postorder(lambda node: print(node))


LEFT = 0
RIGHT = 1

class Node:
    def __init__(self, v):
        self.p = None
        self.c = [None, None]
        self.visited = False

        self.v = v
        self.s = 0
        self.n = 0
    
    def recompute_s(self, r):
        self.n = self.c[LEFT].n + self.c[RIGHT].n + int(self.visited)
        self.s = (
            (r ** self.c[RIGHT].n * (r * self.c[LEFT].s + self.v) 
            if self.visited else r ** self.c[RIGHT].n * self.c[LEFT].s)
            + self.c[RIGHT].s
        )

    def __str__(self):
        return '{} {} {}'.format(self.v, self.s, self.n)

def fast_pp_hist(score_hist, ratio = .95):
    null = Node(0)
    N = len(score_hist)
    ans = []

    import numpy as np
    nodes = list(map(Node, score_hist))
    sorted_i = np.argsort(score_hist)

    def to_bst(start, end, p):
        if start > end: return null
        mid = (start + end) // 2
        node = nodes[sorted_i[mid]]
        node.p = p
        node.c = [to_bst(start, mid - 1, node), to_bst(mid + 1, end, node)]
        return node
    
    root = to_bst(0, N - 1, null)
    for node in nodes:
        node.visited = True
        while node != null:
            node.recompute_s(ratio)
            node = node.p
        ans.append(root.s)
    
    return ans

"""An LRU (least recently used) cache from scratch: a dict for O(1) lookup, plus a
doubly linked list that keeps items in order of use.

    python3 lru.py

  get(key)   look it up in the dict; move its node to the front (most recently used)
  put(key)   add a node at the front; if over capacity, remove the node at the back
             (least recently used) from both the list and the dict

Both are O(1). Python's functools.lru_cache and OrderedDict do the same job; writing it once
shows why two structures are needed: the dict finds a node fast, the list keeps the order.
"""


class Node:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key=None, value=None):
        self.key, self.value, self.prev, self.next = key, value, None, None


class LRUCache:
    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self.map: dict = {}
        self.head, self.tail = Node(), Node()      # sentinels: never hold data
        self.head.next, self.tail.prev = self.tail, self.head
        self.evicted: list = []

    def _unlink(self, node: Node) -> None:
        node.prev.next, node.next.prev = node.next, node.prev

    def _push_front(self, node: Node) -> None:
        node.prev, node.next = self.head, self.head.next
        self.head.next.prev = node
        self.head.next = node

    def get(self, key):
        node = self.map.get(key)
        if node is None:
            return None
        self._unlink(node)
        self._push_front(node)
        return node.value

    def put(self, key, value) -> None:
        if key in self.map:
            node = self.map[key]
            node.value = value
            self._unlink(node)
        else:
            node = Node(key, value)
            self.map[key] = node
            if len(self.map) > self.capacity:
                oldest = self.tail.prev
                self._unlink(oldest)
                del self.map[oldest.key]
                self.evicted.append(oldest.key)
        self._push_front(node)

    def order(self) -> list:
        """Keys from most to least recently used."""
        out, node = [], self.head.next
        while node is not self.tail:
            out.append(node.key)
            node = node.next
        return out


if __name__ == "__main__":
    c = LRUCache(3)
    for step in ["put a", "put b", "put c", "get a", "put d", "get b", "put e"]:
        op, key = step.split()
        result = c.put(key, key.upper()) if op == "put" else c.get(key)
        shown = "" if op == "put" else f" -> {result}"
        print(f"{step:<6}{shown:<8} order (newest first): {c.order()}  evicted so far: {c.evicted}")

"""A binary min-heap from scratch: the structure behind priority queues.

    python3 heap.py

The heap is a list read as a tree: the children of index i are at 2i+1 and 2i+2, and every
parent is <= its children, so the smallest item is always at index 0.

  push   add at the end, then swap upwards while smaller than the parent      O(log n)
  pop    take index 0, move the last item to the top, swap it downwards       O(log n)

Python's heapq module works on exactly this layout; the tests check that both give the same order.
"""


class MinHeap:
    def __init__(self) -> None:
        self.items: list = []

    def push(self, item) -> None:
        self.items.append(item)
        i = len(self.items) - 1
        while i > 0:
            parent = (i - 1) // 2
            if self.items[i] < self.items[parent]:
                self.items[i], self.items[parent] = self.items[parent], self.items[i]
                i = parent
            else:
                break

    def pop(self):
        if not self.items:
            raise IndexError("pop from an empty heap")
        smallest = self.items[0]
        last = self.items.pop()
        if self.items:
            self.items[0] = last
            i = 0
            while True:
                left, right, small = 2 * i + 1, 2 * i + 2, i
                if left < len(self.items) and self.items[left] < self.items[small]:
                    small = left
                if right < len(self.items) and self.items[right] < self.items[small]:
                    small = right
                if small == i:
                    break
                self.items[i], self.items[small] = self.items[small], self.items[i]
                i = small
        return smallest

    def __len__(self) -> int:
        return len(self.items)


def top_k_largest(values, k: int) -> list:
    """Keep a heap of the k largest seen so far: O(n log k), not a full sort."""
    h = MinHeap()
    for v in values:
        h.push(v)
        if len(h) > k:
            h.pop()                     # drop the smallest of the k + 1
    return sorted(h.items, reverse=True)


if __name__ == "__main__":
    h = MinHeap()
    for job in [(3, "send report"), (1, "page on-call"), (2, "retry payment"), (5, "tidy logs"), (1, "restart db")]:
        h.push(job)
        print(f"push {job!s:<22} heap as a list: {[p for p, _ in h.items]}")
    print("pop order:", [h.pop() for _ in range(len(h))])
    print("top 3 of [7, 2, 9, 4, 11, 5]:", top_k_largest([7, 2, 9, 4, 11, 5], 3))

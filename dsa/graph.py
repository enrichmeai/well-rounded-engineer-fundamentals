"""Graph search: breadth-first search for the fewest hops, Dijkstra for the cheapest path.

    python3 graph.py

A graph here is a dict: each node maps to its neighbours (and, for Dijkstra, the cost of each edge).

  BFS        visit nodes in rings of distance 1, 2, 3...; the first time you reach the target
             is by the fewest edges. Uses a queue.                              O(V + E)
  Dijkstra   always expand the cheapest node found so far, using a priority queue (a heap);
             works when every edge cost is zero or more.                       O((V + E) log V)

The example: services calling each other, with latency in ms on each call.
"""

import heapq
from collections import deque

CALLS = {                                   # caller: {callee: latency in ms}
    "gateway": {"auth": 5, "orders": 20, "search": 40, "ledger": 200},   # a direct but slow call
    "auth": {"users": 5},
    "orders": {"payments": 30, "inventory": 10},
    "search": {"inventory": 5},
    "users": {},
    "payments": {"ledger": 15},
    "inventory": {"ledger": 50},
    "ledger": {},
}


def bfs_path(graph: dict, start: str, goal: str) -> list[str] | None:
    queue = deque([[start]])
    seen = {start}
    while queue:
        path = queue.popleft()               # first in, first out: nearest rings first
        node = path[-1]
        if node == goal:
            return path
        for nxt in graph[node]:
            if nxt not in seen:
                seen.add(nxt)
                queue.append(path + [nxt])
    return None


def dijkstra(graph: dict, start: str, goal: str) -> tuple[int, list[str]] | None:
    frontier = [(0, [start])]                # (cost so far, path), cheapest first
    done = set()
    while frontier:
        cost, path = heapq.heappop(frontier)
        node = path[-1]
        if node == goal:
            return cost, path
        if node in done:
            continue
        done.add(node)
        for nxt, weight in graph[node].items():
            if nxt not in done:
                heapq.heappush(frontier, (cost + weight, path + [nxt]))
    return None


if __name__ == "__main__":
    print("fewest calls   gateway -> ledger:", " -> ".join(bfs_path(CALLS, "gateway", "ledger")))
    cost, path = dijkstra(CALLS, "gateway", "ledger")
    print(f"lowest latency gateway -> ledger: {' -> '.join(path)} ({cost} ms)")

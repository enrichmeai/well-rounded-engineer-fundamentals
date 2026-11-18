"""Big O, counted instead of timed: how the number of steps grows with the input.

    python3 big_o.py

Timings depend on your machine; step counts do not. Each function here returns how many
comparisons it made, so you can see the growth directly:

  linear search      O(n)        look at each item until you find it
  binary search      O(log n)    halve a SORTED list each time
  duplicates, nested O(n^2)      compare every pair
  duplicates, set    O(n)        remember what you have seen in a hash set
"""


def linear_search(items: list, target) -> tuple[int, int]:
    """Returns (index or -1, comparisons made)."""
    steps = 0
    for i, item in enumerate(items):
        steps += 1
        if item == target:
            return i, steps
    return -1, steps


def binary_search(sorted_items: list, target) -> tuple[int, int]:
    """The list must be sorted. Returns (index or -1, comparisons made)."""
    lo, hi, steps = 0, len(sorted_items) - 1, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        steps += 1
        if sorted_items[mid] == target:
            return mid, steps
        if sorted_items[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1, steps


def has_duplicate_nested(items: list) -> tuple[bool, int]:
    steps = 0
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            steps += 1
            if items[i] == items[j]:
                return True, steps
    return False, steps


def has_duplicate_set(items: list) -> tuple[bool, int]:
    seen, steps = set(), 0
    for item in items:
        steps += 1                      # one hash-set lookup (average O(1)) per item
        if item in seen:
            return True, steps
        seen.add(item)
    return False, steps


def table(sizes=(10, 100, 1_000, 10_000)) -> list[tuple[int, int, int, int, int]]:
    rows = []
    for n in sizes:
        items = list(range(n))           # sorted, no duplicates: the worst case for every search
        missing = n                      # a value that is not there
        rows.append((n, linear_search(items, missing)[1], binary_search(items, missing)[1],
                     has_duplicate_nested(items)[1], has_duplicate_set(items)[1]))
    return rows


if __name__ == "__main__":
    rows = table()
    print(f"{'n':>9} {'linear':>9} {'binary':>7} {'nested dup':>12} {'set dup':>8}")
    for n, lin, bi, nest, st in rows:
        print(f"{n:>9} {lin:>9} {bi:>7} {nest:>12} {st:>8}")
    first, last = rows[0], rows[-1]
    print(f"\nn grew {last[0] // first[0]:,} times. Steps grew: linear {last[1] / first[1]:,.0f}x, "
          f"binary {last[2] / first[2]:,.1f}x, nested {last[3] / first[3]:,.0f}x, set {last[4] / first[4]:,.0f}x.")

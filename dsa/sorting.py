"""Sorting, counted: insertion sort is O(n^2), merge sort is O(n log n).

    python3 sorting.py

Both functions return the sorted list and the number of comparisons they made. Insertion sort
is fine for a few items (and nearly sorted input); merge sort splits the list in half, sorts each
half, and merges them, so it never needs more than about n log2 n comparisons. Python's own
sorted() uses Timsort, which combines both ideas.
"""

import random


def insertion_sort(items: list) -> tuple[list, int]:
    out, steps = list(items), 0
    for i in range(1, len(out)):
        j = i
        while j > 0:
            steps += 1
            if out[j - 1] <= out[j]:
                break
            out[j - 1], out[j] = out[j], out[j - 1]
            j -= 1
    return out, steps


def merge_sort(items: list) -> tuple[list, int]:
    if len(items) <= 1:
        return list(items), 0
    mid = len(items) // 2
    left, a = merge_sort(items[:mid])
    right, b = merge_sort(items[mid:])
    merged, i, j, steps = [], 0, 0, a + b
    while i < len(left) and j < len(right):
        steps += 1
        if left[i] <= right[j]:
            merged.append(left[i]); i += 1
        else:
            merged.append(right[j]); j += 1
    merged += left[i:] + right[j:]
    return merged, steps


if __name__ == "__main__":
    rng = random.Random(42)                   # fixed seed: the same "random" list every run
    print(f"{'n':>6} {'insertion':>11} {'merge':>8}")
    for n in (10, 100, 1000, 4000):
        data = [rng.randint(0, 10**6) for _ in range(n)]
        print(f"{n:>6} {insertion_sort(data)[1]:>11} {merge_sort(data)[1]:>8}")

"""Quorums: with N replicas, writing to W and reading from R, a read is sure to see the latest
write only when W + R > N, because then every read set overlaps every write set.

    python3 quorum.py

Three replicas hold (version, value). A write goes to the first W replicas that are reachable;
a read asks R replicas and keeps the highest version it sees. One replica is cut off by a
partition during the write and comes back before the read, still holding the old value.
"""

from itertools import combinations

N = 3


class Replica:
    def __init__(self, name: str):
        self.name, self.version, self.value = name, 0, "old"


def write(replicas, value: str, version: int, w: int, unreachable: set[str]) -> list[str]:
    reached = [r for r in replicas if r.name not in unreachable][:w]
    if len(reached) < w:
        raise RuntimeError(f"only {len(reached)} of the {w} replicas needed are reachable: write refused")
    for r in reached:
        r.version, r.value = version, value
    return [r.name for r in reached]


def read(replicas, names: tuple[str, ...]) -> str:
    chosen = [r for r in replicas if r.name in names]
    return max(chosen, key=lambda r: r.version).value


def every_read(w: int, r: int) -> dict[tuple[str, ...], str]:
    """Write 'new' with replica c cut off, heal, then try every possible set of R replicas."""
    replicas = [Replica(n) for n in "abc"]
    write(replicas, "new", version=1, w=w, unreachable={"c"})
    return {names: read(replicas, names) for names in combinations("abc", r)}


if __name__ == "__main__":
    for w, r in [(1, 1), (2, 1), (1, 2), (2, 2), (3, 1)]:
        sign = ">" if w + r > N else "<="
        try:
            results = every_read(w, r)
        except RuntimeError as e:
            print(f"N={N} W={w} R={r}  W+R{sign}N  {e} (consistent, but not available)")
            continue
        stale = ["+".join(n) for n, v in results.items() if v == "old"]
        verdict = "always sees the latest" if not stale else "stale when reading " + ", ".join(stale)
        print(f"N={N} W={w} R={r}  W+R{sign}N  {verdict}")

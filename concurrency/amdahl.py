"""Amdahl's law: how much faster can more processors make a job?

    python3 amdahl.py            # the table for a job that is 90% parallel
    python3 amdahl.py 0.5        # try a job that is only half parallel

If a fraction p of the work can run in parallel on s processors, and the rest must run
one step at a time, the speed-up is

    1 / ((1 - p) + p / s)

The serial part sets a ceiling: however many processors you add, the speed-up never
passes 1 / (1 - p). For p = 0.9 that ceiling is 10.
"""

import sys


def speedup(p: float, s: float) -> float:
    if not 0 <= p <= 1:
        raise ValueError("p is a fraction between 0 and 1")
    if s < 1:
        raise ValueError("s is a number of processors, at least 1")
    return 1 / ((1 - p) + p / s)


def ceiling(p: float) -> float:
    return float("inf") if p == 1 else 1 / (1 - p)


if __name__ == "__main__":
    p = float(sys.argv[1]) if len(sys.argv) > 1 else 0.9
    print(f"p = {p:.0%} parallel")
    for s in (1, 2, 4, 8, 16, 64, 1024):
        print(f"  {s:>5} processors: {speedup(p, s):6.2f}x")
    print(f"  ceiling          : {ceiling(p):6.2f}x")

"""How many machines should you commit to? Work it out from an hour-by-hour week of real usage.

    python3 commit_plan.py                     # the example week below, 30% discount
    python3 commit_plan.py --discount 0.5

A commitment (a committed use discount, a savings plan or a reservation) is a lower price for
agreeing to pay for a fixed amount, whether you use it or not. Anything above the commitment
is paid at the normal on-demand price.

So for each candidate commitment c, over every hour h of the week:

    cost(c) = c x committed_price x hours  +  sum over h of max(0, usage[h] - c) x on_demand_price

The script tries every c and prints the cost of each, so you can see the curve, not only
the answer. It also checks the rule of thumb that falls out of the formula: commit to the
k-th machine only if you use at least k machines in more than (1 - discount) of the hours.

Prices are inputs, not real prices: put in your provider's numbers.
"""

import argparse


def example_week() -> list[int]:
    """168 hours (Monday 00:00 first). A base of 4 machines, 10 in working hours on weekdays,
    and 6 during a nightly batch from 01:00 to 04:00."""
    week = []
    for day in range(7):
        for hour in range(24):
            if day < 5 and 9 <= hour < 18:
                week.append(10)
            elif 1 <= hour < 4:
                week.append(6)
            else:
                week.append(4)
    return week


def cost(usage: list[int], commit: int, on_demand: float, discount: float) -> float:
    committed_price = on_demand * (1 - discount)
    committed = commit * committed_price * len(usage)
    overflow = sum(max(0, u - commit) for u in usage) * on_demand
    return committed + overflow


def best_commit(usage: list[int], on_demand: float, discount: float) -> int:
    """The commitment with the lowest cost (the smallest one, if several tie)."""
    return min(range(max(usage) + 1), key=lambda c: (cost(usage, c, on_demand, discount), c))


def rule_of_thumb(usage: list[int], discount: float) -> int:
    """Commit to machine k while at least k machines are in use in more than (1 - discount) of hours."""
    k = 0
    while sum(u >= k + 1 for u in usage) / len(usage) > 1 - discount:
        k += 1
    return k


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--on-demand", type=float, default=1.00, help="price per machine-hour on demand (default 1.00)")
    p.add_argument("--discount", type=float, default=0.30, help="commitment discount as a fraction (default 0.30)")
    a = p.parse_args()
    week = example_week()
    print(f"example week: {len(week)} hours, min {min(week)}, max {max(week)} machines, "
          f"{sum(week)} machine-hours; on demand {a.on_demand:.2f}, discount {a.discount:.0%}")
    print(" commit  weekly cost")
    best = best_commit(week, a.on_demand, a.discount)
    for c in range(max(week) + 1):
        mark = "  <- lowest" if c == best else ""
        print(f" {c:>6}  {cost(week, c, a.on_demand, a.discount):>11.2f}{mark}")
    print(f"no commitment: {cost(week, 0, a.on_demand, a.discount):.2f}; best: commit {best}, "
          f"saving {cost(week, 0, a.on_demand, a.discount) - cost(week, best, a.on_demand, a.discount):.2f} a week")
    print(f"rule of thumb gives {rule_of_thumb(week, a.discount)}: use at least that many in more than "
          f"{1 - a.discount:.0%} of hours")

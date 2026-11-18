"""Read a cloud bill and answer the first questions anyone should ask of it.

    python3 bill.py                      # the made-up sample bill in this folder
    python3 bill.py my_bill.csv --tag team

It reads a CSV whose columns are named as in FOCUS, the FinOps Open Cost and Usage
Specification (an open format for cost data): ServiceName, ResourceId, Tags (a JSON
object), BilledCost and ChargeCategory (Usage, Purchase, Tax, Credit or Adjustment).
Many providers can export their bills in this format; the sample here is invented.

It answers:
  1. what the total is, and how much is usage versus other charges
  2. which services cost most
  3. who owns the cost, by a tag such as "team", and how much has no owner
  4. which single resources cost most
"""

import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(path: Path) -> list[dict]:
    """Read the CSV. Money is kept as Decimal, so pennies do not drift as they would with floats."""
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["BilledCost"] = Decimal(row["BilledCost"])
        row["Tags"] = json.loads(row["Tags"] or "{}")
    return rows


def total(rows: list[dict]) -> Decimal:
    return sum((r["BilledCost"] for r in rows), Decimal("0"))


def by(rows: list[dict], key) -> list[tuple[str, Decimal]]:
    """Sum BilledCost by a key function; largest first."""
    sums: dict[str, Decimal] = defaultdict(Decimal)
    for r in rows:
        sums[key(r)] += r["BilledCost"]
    return sorted(sums.items(), key=lambda kv: kv[1], reverse=True)


def report(rows: list[dict], tag: str = "team", top: int = 3) -> str:
    usage = [r for r in rows if r["ChargeCategory"] == "Usage"]
    lines = [f"total billed: {total(rows):.2f}  (usage {total(usage):.2f}, other charges {total(rows) - total(usage):.2f})",
             "", "by charge category:"]
    lines += [f"  {name:<12} {cost:>9.2f}" for name, cost in by(rows, lambda r: r["ChargeCategory"])]
    lines += ["", "usage by service:"]
    lines += [f"  {name:<14} {cost:>9.2f}" for name, cost in by(usage, lambda r: r["ServiceName"])]
    lines += ["", f"usage by tag '{tag}':"]
    owners = by(usage, lambda r: r["Tags"].get(tag, "(untagged)"))
    lines += [f"  {name:<14} {cost:>9.2f}" for name, cost in owners]
    untagged = dict(owners).get("(untagged)", Decimal("0"))
    if total(usage):
        lines.append(f"  {untagged / total(usage):.0%} of usage has no '{tag}' tag: nobody is answerable for it")
    lines += ["", f"top {top} resources by usage cost:"]
    lines += [f"  {name:<14} {cost:>9.2f}" for name, cost in by(usage, lambda r: r["ResourceId"])[:top]]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv", nargs="?", default=HERE / "sample_bill.csv", type=Path)
    parser.add_argument("--tag", default="team", help="the tag key that names an owner (default: team)")
    args = parser.parse_args()
    print(report(load(args.csv), tag=args.tag))

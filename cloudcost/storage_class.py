"""Which storage class is cheapest for your data? It depends on how often you read it, and for how long you keep it.

    python3 storage_class.py

Colder storage classes cost less to keep and more to read, and many have a minimum storage
duration: delete or move an object sooner and you are still charged for the minimum. (Google
Cloud Storage, for example, has minimums of 30, 90 and 365 days for Nearline, Coldline and
Archive.)

The prices below are MADE UP, round numbers chosen so the arithmetic is easy to follow. Put in
your provider's price list before you decide anything.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StorageClass:
    name: str
    per_gb_month: float     # keeping a GB for a month
    per_gb_read: float      # reading (retrieving) a GB
    min_days: int           # charged for at least this long


EXAMPLE_CLASSES = [
    StorageClass("hot", 0.020, 0.000, 0),
    StorageClass("cool", 0.010, 0.010, 30),
    StorageClass("cold", 0.004, 0.020, 90),
    StorageClass("archive", 0.0012, 0.050, 365),
]


def cost(c: StorageClass, gb: float, days_kept: int, gb_read_per_month: float) -> float:
    """Total cost of keeping `gb` for `days_kept` days and reading `gb_read_per_month` each month."""
    billed_days = max(days_kept, c.min_days)          # the minimum storage duration
    months_kept = days_kept / 30
    keep = gb * c.per_gb_month * billed_days / 30
    read = gb_read_per_month * months_kept * c.per_gb_read
    return keep + read


def cheapest(classes, gb, days_kept, gb_read_per_month) -> StorageClass:
    return min(classes, key=lambda c: cost(c, gb, days_kept, gb_read_per_month))


SCENARIOS = [
    ("1 TB of images, read in full twice a month, kept a year", 1000, 365, 2000),
    ("1 TB of logs, read 10 GB a month, kept a year", 1000, 365, 10),
    ("1 TB of backups, never read, kept a year", 1000, 365, 0),
    ("1 TB of backups, never read, deleted after 30 days", 1000, 30, 0),
]


if __name__ == "__main__":
    print("MADE-UP prices: replace them with your provider's before deciding.\n")
    for label, gb, days, reads in SCENARIOS:
        print(label)
        for c in EXAMPLE_CLASSES:
            print(f"  {c.name:<8} {cost(c, gb, days, reads):>9.2f}")
        print(f"  cheapest: {cheapest(EXAMPLE_CLASSES, gb, days, reads).name}\n")

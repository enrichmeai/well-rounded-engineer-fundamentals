"""What does switching a machine off outside working hours save?

    python3 schedule.py                          # 8 hours a day, 5 days a week, at 1.00 an hour
    python3 schedule.py --hours 10 --days 5 --price 0.40

A machine left on all week runs 24 x 7 = 168 hours. A development machine used only in working
hours might be needed for 40 of them. AWS's cost guidance uses this example and puts the
potential saving at 75%; the exact figure is 1 - 40/168, about 76%.
"""

import argparse

HOURS_IN_WEEK = 24 * 7


def saving(hours_per_day: float, days_per_week: int) -> float:
    on = hours_per_day * days_per_week
    if not 0 <= on <= HOURS_IN_WEEK:
        raise ValueError("a week has 168 hours")
    return 1 - on / HOURS_IN_WEEK


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--hours", type=float, default=8, help="hours on per working day (default 8)")
    p.add_argument("--days", type=int, default=5, help="working days per week (default 5)")
    p.add_argument("--price", type=float, default=1.00, help="price per hour (default 1.00)")
    a = p.parse_args()
    on = a.hours * a.days
    print(f"always on : {HOURS_IN_WEEK} h a week, {HOURS_IN_WEEK * a.price:.2f}")
    print(f"scheduled : {on:g} h a week, {on * a.price:.2f}")
    print(f"saving    : {saving(a.hours, a.days):.0%} ({(HOURS_IN_WEEK - on) * a.price:.2f} a week, "
          f"{(HOURS_IN_WEEK - on) * a.price * 52:.2f} a year)")

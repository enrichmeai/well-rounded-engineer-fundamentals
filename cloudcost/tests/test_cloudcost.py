"""Tests for the cloud cost tools. Standard library plus pytest; no cloud account, no network."""

import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bill  # noqa: E402
import commit_plan  # noqa: E402
import schedule  # noqa: E402
import storage_class  # noqa: E402

SAMPLE = Path(__file__).resolve().parent.parent / "sample_bill.csv"


def test_bill_totals_are_exact_decimals():
    rows = bill.load(SAMPLE)
    assert bill.total(rows) == Decimal("3104.75")
    usage = [r for r in rows if r["ChargeCategory"] == "Usage"]
    assert bill.total(usage) == Decimal("2969.75")


def test_bill_groups_by_service_and_owner():
    usage = [r for r in bill.load(SAMPLE) if r["ChargeCategory"] == "Usage"]
    assert bill.by(usage, lambda r: r["ServiceName"])[0] == ("Compute", Decimal("1536.80"))
    owners = dict(bill.by(usage, lambda r: r["Tags"].get("team", "(untagged)")))
    assert owners == {"shop": Decimal("1891.80"), "data": Decimal("687.30"), "(untagged)": Decimal("390.65")}


def test_report_names_the_untagged_share():
    text = bill.report(bill.load(SAMPLE))
    assert "13% of usage has no 'team' tag" in text
    assert "db-orders" in text


def test_commitment_cost_formula_by_hand():
    usage = [2, 2, 5, 5]                       # four hours
    # commit 2 at 30% off: 2 x 0.7 x 4 hours = 5.6, plus overflow (3 + 3) x 1.0 = 6.0
    assert commit_plan.cost(usage, 2, on_demand=1.0, discount=0.3) == pytest.approx(11.6)
    assert commit_plan.cost(usage, 0, on_demand=1.0, discount=0.3) == pytest.approx(14.0)


@pytest.mark.parametrize("discount", [0.1, 0.3, 0.5, 0.6, 0.72])
def test_best_commitment_matches_the_rule_of_thumb(discount):
    week = commit_plan.example_week()
    assert commit_plan.best_commit(week, 1.0, discount) == commit_plan.rule_of_thumb(week, discount)


def test_committing_to_the_peak_can_cost_more_than_none():
    week = commit_plan.example_week()
    assert commit_plan.cost(week, max(week), 1.0, 0.3) > commit_plan.cost(week, 0, 1.0, 0.3)


def test_example_week_shape():
    week = commit_plan.example_week()
    assert len(week) == 168 and min(week) == 4 and max(week) == 10


def test_schedule_saving_matches_the_aws_example():
    assert schedule.saving(8, 5) == pytest.approx(1 - 40 / 168)
    assert round(schedule.saving(8, 5), 2) == 0.76
    with pytest.raises(ValueError):
        schedule.saving(25, 7)


def test_minimum_storage_duration_is_charged():
    archive = next(c for c in storage_class.EXAMPLE_CLASSES if c.name == "archive")
    # Kept 30 days but billed for 365.
    assert storage_class.cost(archive, 1000, 30, 0) == pytest.approx(1000 * archive.per_gb_month * 365 / 30)


@pytest.mark.parametrize("label,gb,days,reads,expected", [
    (s[0], s[1], s[2], s[3], e)
    for s, e in zip(storage_class.SCENARIOS, ["hot", "archive", "archive", "cool"])
])
def test_cheapest_class_per_scenario(label, gb, days, reads, expected):
    assert storage_class.cheapest(storage_class.EXAMPLE_CLASSES, gb, days, reads).name == expected

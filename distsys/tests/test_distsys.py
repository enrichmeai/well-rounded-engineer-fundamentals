"""Tests for the distributed systems examples. Everything runs on the seeded simulator, so every
result here is exact, not "usually"."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dst  # noqa: E402
import idempotency  # noqa: E402
import lamport  # noqa: E402
import quorum  # noqa: E402
import two_phase_commit as tpc  # noqa: E402
from sim import Network, Node  # noqa: E402


class Echo(Node):
    def __init__(self):
        self.got = []

    def receive(self, src, body):
        self.got.append((self.net.now, body["n"]))


def _run(seed):
    net = Network(seed=seed, drop=0.2, duplicate=0.2)
    a, b = Echo(), Echo()
    net.add("a", a)
    net.add("b", b)
    for n in range(50):
        a.send("b", {"type": "x", "n": n})
    net.run()
    return b.got, net.log


def test_same_seed_same_run():
    assert _run(42) == _run(42)


def test_different_seeds_differ():
    assert _run(1)[0] != _run(2)[0]


def test_partition_loses_messages_until_healed():
    net = Network(seed=0)
    a, b = Echo(), Echo()
    net.add("a", a)
    net.add("b", b)
    net.cut("a", "b")
    a.send("b", {"type": "x", "n": 1})
    net.heal()
    a.send("b", {"type": "x", "n": 2})
    net.run()
    assert [n for _, n in b.got] == [2]


def test_retries_double_charge_without_an_idempotency_key():
    naive, _ = idempotency.run(idempotency.NaivePayments)
    safe, _ = idempotency.run(idempotency.IdempotentPayments)
    assert naive > 2000
    assert safe == 2000


def test_idempotent_service_is_exact_for_many_seeds():
    for seed in range(50):
        assert idempotency.run(idempotency.IdempotentPayments, seed=seed)[0] == 2000


def test_lamport_order_respects_causality_and_wall_clock_does_not():
    events = lamport.run()
    by_lamport = [e[0] for e in sorted(events, key=lambda e: e[2])]
    by_wall = [e[0] for e in sorted(events, key=lambda e: e[1])]
    causal = ["A sends request", "B receives request", "B sends reply",
              "A receives reply", "A tells C", "C receives notice"]
    assert by_lamport == causal
    assert by_wall.index("B receives request") < by_wall.index("A sends request")   # effect before cause


def test_quorum_overlap_rule():
    for w in (1, 2):
        for r in (1, 2):
            reads = quorum.every_read(w, r)
            always_latest = all(v == "new" for v in reads.values())
            assert always_latest == (w + r > quorum.N)


def test_full_write_quorum_is_refused_during_a_partition():
    try:
        quorum.every_read(3, 1)
    except RuntimeError as e:
        assert "write refused" in str(e)
    else:
        raise AssertionError("W=3 should be refused while a replica is unreachable")


def test_two_phase_commit_outcomes():
    assert set(tpc.run().values()) == {"committed"}
    assert set(tpc.run(votes=(True, False)).values()) == {"aborted"}
    assert set(tpc.run(crash_after_votes=True).values()) == {"prepared"}   # blocked


def test_simulation_finds_the_bug_and_replays_it():
    failing = dst.search(dst.BuggyStore)
    assert failing, "the search should find at least one failing schedule"
    ok, log = dst.simulate(dst.BuggyStore, failing[0])
    assert not ok
    assert dst.simulate(dst.BuggyStore, failing[0]) == (ok, log)        # exact replay
    assert any("value=1" in line for line in log[log.index(next(l for l in log if "value=2" in l)):])


def test_versioned_store_passes_every_schedule():
    assert dst.search(dst.FixedStore) == []

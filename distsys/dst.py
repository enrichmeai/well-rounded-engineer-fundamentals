"""Deterministic simulation testing: run a system under thousands of seeded network schedules,
check an invariant after each, and replay any failure exactly from its seed.

    python3 dst.py

The system: a client sets a key to 1, then to 2, through a network that sometimes delivers a
message twice and delays messages by different amounts. The invariant: once the client has seen
its last write acknowledged, the store must hold 2.

  buggy store   applies every write it receives, in arrival order
  fixed store   writes carry a version number; a store ignores a write older than what it holds

The bug only shows when a duplicate of the first write is delayed until after the second, so a
normal test run will rarely hit it. A simulation tries many schedules in seconds, and because each
schedule comes from a seed, the one that failed can be run again, message for message.

The approach follows Unmesh Joshi's article "Deterministic Simulation Testing" (martinfowler.com),
which draws on FoundationDB and TigerBeetle.
"""

from sim import Network, Node


class Client(Node):
    def __init__(self):
        self.acked: set[int] = set()

    def start(self) -> None:
        self.send("store", {"type": "set", "value": 1, "version": 1})

    def receive(self, src: str, body: dict) -> None:
        first_ack = body["version"] not in self.acked
        self.acked.add(body["version"])
        if body["version"] == 1 and first_ack:        # first write confirmed: send the second, once
            self.send("store", {"type": "set", "value": 2, "version": 2})


class BuggyStore(Node):
    def __init__(self):
        self.value = None

    def receive(self, src: str, body: dict) -> None:
        self.value = body["value"]                     # last arrival wins, even if it is old
        self.send(src, {"type": "ack", "version": body["version"]})


class FixedStore(Node):
    def __init__(self):
        self.value, self.version = None, 0

    def receive(self, src: str, body: dict) -> None:
        if body["version"] > self.version:             # never go back to an older write
            self.value, self.version = body["value"], body["version"]
        self.send(src, {"type": "ack", "version": body["version"]})


def simulate(store_class, seed: int) -> tuple[bool, list[str]]:
    """One seeded run. Returns (invariant held, the message log)."""
    net = Network(seed=seed, duplicate=0.05, max_delay=30)
    client, store = Client(), store_class()
    net.add("client", client)
    net.add("store", store)
    client.start()
    net.run()
    ok = 2 not in client.acked or store.value == 2
    return ok, net.log


def search(store_class, seeds=range(1000)) -> list[int]:
    return [seed for seed in seeds if not simulate(store_class, seed)[0]]


if __name__ == "__main__":
    failing = search(BuggyStore)
    print(f"buggy store: invariant broken in {len(failing)} of 1000 seeds, first at seed {failing[0]}")
    ok, log = simulate(BuggyStore, failing[0])
    print(f"replay seed {failing[0]}:")
    for line in log:
        print("   ", line)
    again = simulate(BuggyStore, failing[0])[1]
    print(f"replaying it again gives the identical log: {again == log}")
    print(f"fixed store: invariant broken in {len(search(FixedStore))} of 1000 seeds")

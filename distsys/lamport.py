"""Ordering events across machines: wall clocks can put an effect before its cause; Lamport clocks cannot.

    python3 lamport.py

Three servers log events. Their wall clocks disagree, as real clocks do: B runs 40 ms behind A,
and C 15 ms ahead. A sends a request to B; B replies to A; A then tells C.

  wall clock      each event stamped with the machine's own time of day
  Lamport clock   a counter: +1 for each local event; every message carries the counter, and a
                  receiver sets its counter to max(own, received) + 1

Lamport's rule guarantees: if event x caused event y (through any chain of messages), then
L(x) < L(y). Sorting by wall clock gives no such guarantee.
"""

from sim import Network, Node

SKEW = {"A": 0, "B": -40, "C": +15}             # ms each machine's clock is off from real time


class Server(Node):
    def __init__(self):
        self.lamport = 0
        self.events: list[tuple[str, int, int]] = []    # (what, wall clock, Lamport)

    def record(self, what: str) -> int:
        self.lamport += 1
        self.events.append((what, self.net.now + SKEW[self.name], self.lamport))
        return self.lamport

    def send_event(self, dst: str, what: str, kind: str) -> None:
        stamp = self.record(what)
        self.send(dst, {"type": kind, "lamport": stamp})

    def receive(self, src: str, body: dict) -> None:
        self.lamport = max(self.lamport, body["lamport"])   # catch up with the sender
        if body["type"] == "request":
            self.record("B receives request")
            self.send_event(src, "B sends reply", "reply")
        elif body["type"] == "reply":
            self.record("A receives reply")
            self.send_event("C", "A tells C", "notice")
        elif body["type"] == "notice":
            self.record("C receives notice")


def run(seed: int = 1) -> list[tuple[str, int, int]]:
    net = Network(seed=seed, max_delay=10)
    for name in "ABC":
        net.add(name, Server())
    net.nodes["A"].send_event("B", "A sends request", "request")
    net.run()
    return [e for name in "ABC" for e in net.nodes[name].events]


if __name__ == "__main__":
    events = run()
    print("sorted by wall clock (what the logs say):")
    for what, wall, lam in sorted(events, key=lambda e: e[1]):
        print(f"  wall {wall:>4} ms  {what}")
    print("sorted by Lamport clock (respects cause and effect):")
    for what, wall, lam in sorted(events, key=lambda e: e[2]):
        print(f"  L={lam}         {what}")

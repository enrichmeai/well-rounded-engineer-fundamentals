"""A tiny deterministic network simulator: the engine every example in this folder runs on.

There are no threads, sockets or real clocks here. There is a list of messages in flight, a
simulated clock, and one random-number generator with a SEED. The network can delay, drop or
duplicate messages, but every choice comes from that one generator, so the same seed gives the
same run, message for message, every time. That is the core idea of deterministic simulation
testing: when a run fails, you rerun its seed and watch exactly the same failure.
"""

import heapq
import random
from dataclasses import dataclass, field


def describe(body: dict) -> str:
    """A message as one short line: its type, then its other fields."""
    rest = " ".join(f"{k}={v}" for k, v in body.items() if k != "type")
    return f"{body.get('type')} {rest}".strip()


@dataclass(order=True)
class Message:
    deliver_at: int
    seq: int                                     # tie-breaker: keeps the order stable
    src: str = field(compare=False)
    dst: str = field(compare=False)
    body: dict = field(compare=False)


class Network:
    """Messages wait in a priority queue ordered by delivery time; the clock jumps to the next one."""

    def __init__(self, seed: int, drop: float = 0.0, duplicate: float = 0.0, max_delay: int = 10):
        self.rng = random.Random(seed)
        self.drop, self.duplicate, self.max_delay = drop, duplicate, max_delay
        self.now = 0
        self.queue: list[Message] = []
        self.seq = 0
        self.nodes: dict[str, object] = {}
        self.partitioned: set[frozenset] = set()
        self.log: list[str] = []

    def add(self, name: str, node) -> None:
        self.nodes[name] = node
        node.net, node.name = self, name

    def cut(self, a: str, b: str) -> None:
        """A partition: messages between a and b are lost until heal()."""
        self.partitioned.add(frozenset((a, b)))

    def heal(self) -> None:
        self.partitioned.clear()

    def send(self, src: str, dst: str, body: dict) -> None:
        if frozenset((src, dst)) in self.partitioned or self.rng.random() < self.drop:
            self.log.append(f"t={self.now:<4} {src}->{dst} {describe(body)}  LOST")
            return
        copies = 2 if self.rng.random() < self.duplicate else 1
        for _ in range(copies):
            self.seq += 1
            delay = self.rng.randint(1, self.max_delay)
            heapq.heappush(self.queue, Message(self.now + delay, self.seq, src, dst, dict(body)))

    def set_timer(self, node: str, delay: int, body: dict) -> None:
        """A timer is a message a node sends itself; the network never loses it."""
        self.seq += 1
        heapq.heappush(self.queue, Message(self.now + delay, self.seq, node, node, dict(body)))

    def run(self, until: int = 10_000) -> None:
        """Deliver messages in time order until none are left (or the clock passes `until`)."""
        while self.queue and self.queue[0].deliver_at <= until:
            msg = heapq.heappop(self.queue)
            self.now = msg.deliver_at
            if msg.src != msg.dst:                   # timers are not network traffic
                self.log.append(f"t={self.now:<4} {msg.src}->{msg.dst} {describe(msg.body)}")
            self.nodes[msg.dst].receive(msg.src, msg.body)


class Node:
    """Base class: a node reacts to messages and can send its own."""

    net: Network
    name: str

    def send(self, dst: str, body: dict) -> None:
        self.net.send(self.name, dst, body)

    def after(self, delay: int, body: dict) -> None:
        self.net.set_timer(self.name, delay, body)

    def receive(self, src: str, body: dict) -> None:   # pragma: no cover - overridden
        raise NotImplementedError

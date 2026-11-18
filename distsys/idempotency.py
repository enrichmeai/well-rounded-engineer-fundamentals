"""Retries plus a lost reply equals a double charge, unless the request carries an idempotency key.

    python3 idempotency.py

A client asks a payment service to charge 100. If no reply arrives within a timeout, it cannot
tell "the request was lost" from "the reply was lost", so it sends the request again. If it was
the reply that was lost, the service sees the same charge twice.

  naive service        charges every request it receives
  idempotent service   remembers each request's idempotency key and returns the first result

The network here loses 30% of messages. The run is seeded, so it is the same every time.
"""

from sim import Network, Node


class Client(Node):
    def __init__(self, charges: int, timeout: int = 25):
        self.pending = {f"order-{i}": 100 for i in range(charges)}   # key -> amount still unconfirmed
        self.timeout = timeout
        self.attempts = 0

    def start(self) -> None:
        for key in list(self.pending):
            self._try(key)

    def _try(self, key: str) -> None:
        self.attempts += 1
        self.send("payments", {"type": "charge", "key": key, "amount": self.pending[key]})
        self.after(self.timeout, {"type": "timeout", "key": key})

    def receive(self, src: str, body: dict) -> None:
        if body["type"] == "ok":
            self.pending.pop(body["key"], None)          # confirmed: stop retrying
        elif body["type"] == "timeout" and body["key"] in self.pending:
            self._try(body["key"])                        # no reply yet: send again


class NaivePayments(Node):
    def __init__(self):
        self.charged = 0

    def receive(self, src: str, body: dict) -> None:
        self.charged += body["amount"]                   # every copy is charged
        self.send(src, {"type": "ok", "key": body["key"]})


class IdempotentPayments(Node):
    def __init__(self):
        self.charged = 0
        self.done: dict[str, dict] = {}                  # key -> the reply already given

    def receive(self, src: str, body: dict) -> None:
        if body["key"] not in self.done:                 # first time: do the work
            self.charged += body["amount"]
            self.done[body["key"]] = {"type": "ok", "key": body["key"]}
        self.send(src, self.done[body["key"]])           # a retry gets the same answer


def run(service_class, charges: int = 20, seed: int = 7, drop: float = 0.3) -> tuple[int, int]:
    net = Network(seed=seed, drop=drop)
    client, service = Client(charges), service_class()
    net.add("client", client)
    net.add("payments", service)
    client.start()
    net.run()
    assert not client.pending, "every charge is eventually confirmed"
    return service.charged, client.attempts


if __name__ == "__main__":
    expected = 20 * 100
    for cls in (NaivePayments, IdempotentPayments):
        charged, attempts = run(cls)
        print(f"{cls.__name__:<19} customer owed {expected}, charged {charged} "
              f"({attempts} requests sent for 20 orders)")

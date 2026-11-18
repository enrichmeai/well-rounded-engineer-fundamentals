"""Two-phase commit, and why it blocks when the coordinator fails at the wrong moment.

    python3 two_phase_commit.py

A transfer must debit one bank's ledger and credit another's, or do neither.

  phase 1 (prepare)  the coordinator asks each participant: can you commit? A participant
                     that votes yes must hold its locks and wait: it has promised to commit if told.
  phase 2 (decide)   if every vote is yes, the coordinator sends commit; otherwise abort.

If the coordinator crashes after the votes but before sending its decision, a participant that
voted yes cannot decide alone: committing might break atomicity if another voted no; aborting
might break it if the coordinator had already told someone to commit. So it waits, holding its
locks, until the coordinator comes back.
"""

from sim import Network, Node


class Participant(Node):
    def __init__(self, vote_yes: bool = True):
        self.vote_yes = vote_yes
        self.state = "idle"                        # idle -> prepared (locks held) -> committed / aborted

    def receive(self, src: str, body: dict) -> None:
        if body["type"] == "prepare":
            self.state = "prepared" if self.vote_yes else "aborted"
            self.send(src, {"type": "vote", "yes": self.vote_yes})
        elif body["type"] in ("commit", "abort"):
            self.state = "committed" if body["type"] == "commit" else "aborted"


class Coordinator(Node):
    def __init__(self, participants: list[str], crash_after_votes: bool = False):
        self.participants = participants
        self.crash_after_votes = crash_after_votes
        self.votes: dict[str, bool] = {}
        self.decision: str | None = None
        self.crashed = False

    def start(self) -> None:
        for p in self.participants:
            self.send(p, {"type": "prepare"})

    def receive(self, src: str, body: dict) -> None:
        if self.crashed:
            return
        self.votes[src] = body["yes"]
        if len(self.votes) == len(self.participants):
            if self.crash_after_votes:
                self.crashed = True                 # every vote is in; the decision is never sent
                return
            self.decision = "commit" if all(self.votes.values()) else "abort"
            for p in self.participants:
                self.send(p, {"type": self.decision})


def run(votes=(True, True), crash_after_votes: bool = False, seed: int = 3) -> dict[str, str]:
    net = Network(seed=seed)
    names = [f"bank-{i + 1}" for i in range(len(votes))]
    for name, yes in zip(names, votes):
        net.add(name, Participant(yes))
    coordinator = Coordinator(names, crash_after_votes)
    net.add("coordinator", coordinator)
    coordinator.start()
    net.run()
    return {name: net.nodes[name].state for name in names}


if __name__ == "__main__":
    print("both vote yes                       :", run())
    print("bank-2 votes no                     :", run(votes=(True, False)))
    print("coordinator crashes after the votes :", run(crash_after_votes=True),
          "<- both stuck holding their locks")

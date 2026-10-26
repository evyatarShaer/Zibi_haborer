"""Case-store helpers for the P2B-5 tests: a settable clock and short case steps."""
HOUR, DAY = 3600, 24 * 3600
CASE = ("פיצה", "דנה", "יוסי", "פיצה עם אננס זה טעים")
TEXT_B = "אננס על פיצה זה פשע"


def result(outcome="win", winner="A"):
    """Shape of borer_sim.hearing.run's result."""
    metrics = {"A": 30.0, "B": 20.0, "gap": 0.2, "winner": winner, "outcome": outcome}
    return {"seed": 5, "mood": {}, "metrics": metrics, "brain": {"bin_ms": 50, "mn9_hz": [[1.0], [2.0]]},
            "sim_version": "0.9.0", "platform": "test", "duration_ms": 7000}


class Clock:
    def __init__(self):
        self.t = 1_000_000_000.0

    def __call__(self):
        return self.t


def opened(store, ip="1.2.3.4"):
    return store.open(*CASE, ip=ip)


def decide(store, hid, outcome="win", winner="A"):
    store.start(hid)
    store.finish(hid, result(outcome, winner))


def decided_case(store, clock):
    c = opened(store)
    clock.t += HOUR
    decide(store, store.submit_b(c["id"], TEXT_B, seed=1))
    return c

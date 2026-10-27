"""Appeals (P2B-6): once per side, within 3 h of the latest verdict, at most 3 hearings,
a fresh seed on the original arguments; "accepted" against the previous verdict."""
import pytest

from apikit import decided, device, open_case, settled
from borer_api import views
from fake import BRAIN, OK, TEXT_B

HOUR = 3600


def appeal(client, case, side):
    return client.post(f"/api/{side}/{case[side]}/appeal")


@pytest.fixture
def case(client):
    return open_case(client)


def test_each_side_once_then_final(client, sim, case):
    b, _ = decided(client, case)
    assert appeal(client, case, "a").status_code == 201
    r = appeal(b, case, "b")  # the appeal is still being heard
    assert r.status_code == 409 and r.json()["error"] == views.NOT_DECIDED
    settled(client, f"/api/a/{case['a']}", 1)
    r = appeal(client, case, "a")
    assert r.status_code == 409 and r.json()["error"] == views.APPEALED
    assert appeal(b, case, "b").status_code == 201
    a = settled(client, f"/api/a/{case['a']}", 2)
    assert [(h["n"], h["appealed_by"]) for h in a["hearings"]] == [(0, None), (1, "A"), (2, "B")]
    assert not a["can_appeal"] and not b.get(f"/api/b/{case['b']}").json()["can_appeal"]
    assert appeal(client, case, "a").status_code == 409 and appeal(b, case, "b").status_code == 409
    assert len(sim.calls) == 3  # no 4th hearing
    texts = {c[:2] for c in sim.calls}
    seeds = {c[2] for c in sim.calls}
    assert texts == {(OK["text_a"], TEXT_B)} and len(seeds) == 3
    assert {c[3] for c in sim.calls} == {0.0}  # the case's own wait, every time


def test_appeal_window_is_3_hours_from_the_latest_verdict(client, clock, case):
    b, _ = decided(client, case)
    clock.t += 3 * HOUR
    assert client.get(f"/api/a/{case['a']}").json()["appeal_closes_in_s"] == 0
    assert appeal(client, case, "a").status_code == 201
    settled(client, f"/api/a/{case['a']}", 1)
    assert b.get(f"/api/b/{case['b']}").json()["can_appeal"]  # the window restarts
    clock.t += 3 * HOUR + 1  # 3 h after the appeal's verdict, not the first one
    assert b.get(f"/api/b/{case['b']}").json()["can_appeal"] is False
    r = appeal(b, case, "b")
    assert r.status_code == 409 and r.json()["error"] == views.APPEAL_LATE


def test_only_a_may_appeal_a_no_show(client, clock, case):
    clock.t += 3 * HOUR
    settled(client, f"/api/a/{case['a']}", 0)
    b = device(client)
    b.get(f"/api/b/{case['b']}")
    r = appeal(b, case, "b")
    assert r.status_code == 409 and r.json()["error"] == views.NO_SHOW_ONLY_A
    assert appeal(client, case, "a").status_code == 201
    a = settled(client, f"/api/a/{case['a']}", 1)
    assert a["status"] == "no_show" and a["hearings"][1]["wait_h"] == 3.0


@pytest.mark.parametrize("verdicts, accepted", [
    ([("win", "A"), ("win", "B"), ("win", "B")], [True, False]),   # against the previous one
    ([("win", "A"), ("dithered", "A")], [False]),                   # same side, other outcome
    ([("win", "A"), ("tie", "A")], [True]),                         # a side → no winner
    ([("tie", "A"), ("froze", "B")], [False]),                      # no winner both times
    ([("food", "B"), ("dithered", "B"), ("win", "A")], [True, True]),
])
def test_accepted_uses_the_previous_verdicts_winner(client, sim, case, verdicts, accepted):
    sim.outcome, sim.winner = verdicts[0]
    b, _ = decided(client, case)
    for n, (v, side) in enumerate(zip(verdicts[1:], ("a", "b")), start=1):
        sim.outcome, sim.winner = v
        appeal(b if side == "b" else client, case, side)
        a = settled(client, f"/api/a/{case['a']}", n)
    assert [h["accepted"] for h in a["hearings"][1:]] == accepted
    assert "accepted" not in a["hearings"][0]


def test_brain_is_stored_data_for_parties_only(client, sim, case):
    b, _ = decided(client, case)
    calls = len(sim.calls)
    want = {k: v for k, v in BRAIN.items() if k != "taste_hz"}
    for _ in range(2):
        assert client.get(f"/api/a/{case['a']}/brain/0").json() == want
        assert b.get(f"/api/b/{case['b']}/brain/0").json() == want
    assert len(sim.calls) == calls
    assert client.get(f"/api/a/{case['a']}/brain/1").status_code == 404
    assert client.get(f"/api/b/{case['b']}/brain/0").status_code == 409  # A's device on B's link

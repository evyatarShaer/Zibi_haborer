"""Appeal (P2A-7) and brain view (P2A-8) API, with a fake simulation."""
import pytest

from borer_api import court, views
from fake import BRAIN, OK, wait_status


def decided(client, body=OK):
    return wait_status(client, client.post("/hearing", json=body).json()["id"], "decided")


def appeal(client, hid):
    return client.post(f"/hearing/{hid}/appeal")


def test_appeal_reruns_same_case_with_new_seed(client, sim):
    orig = decided(client)
    r = appeal(client, orig["id"])
    assert r.status_code == 201
    a = wait_status(client, r.json()["id"], "decided")
    assert a["appeal_of"] == orig["id"] and not a["can_appeal"] and a["appeal_id"] is None
    assert {k: a[k] for k in ("topic", "name_a", "name_b", "text_a", "text_b")} == \
        {k: orig[k] for k in ("topic", "name_a", "name_b", "text_a", "text_b")}
    assert sim.calls[1][:2] == sim.calls[0][:2] and sim.calls[1][2] != sim.calls[0][2]
    again = client.get(f"/hearing/{orig['id']}").json()
    assert not again["can_appeal"] and again["appeal_id"] == a["id"]
    assert "appeal_accepted" not in again


def test_second_appeal_and_appeal_of_appeal_refused(client):
    orig = decided(client)
    first = appeal(client, orig["id"]).json()["id"]
    r = appeal(client, orig["id"])
    assert r.status_code == 409 and r.json()["error"] == views.APPEALED
    wait_status(client, first, "decided")
    r = appeal(client, first)
    assert r.status_code == 409 and r.json()["error"] == views.APPEAL_OF_APPEAL


def test_appeal_needs_a_decided_hearing(client, sim):
    assert appeal(client, "nope").status_code == 404
    sim.gate.clear()
    hid = client.post("/hearing", json=OK).json()["id"]
    r = appeal(client, hid)
    assert r.status_code == 409 and r.json()["error"] == views.NOT_DECIDED
    sim.gate.set()
    wait_status(client, hid, "decided")
    assert appeal(client, hid).status_code == 201


@pytest.mark.parametrize("before, after, accepted", [
    (("win", "A"), ("win", "B"), True),
    (("win", "A"), ("dithered", "A"), False),     # same winner, other outcome
    (("win", "A"), ("tie", "A"), True),           # a side → no winner
    (("tie", "A"), ("froze", "B"), False),        # no winner both times
    (("food", "B"), ("dithered", "B"), True),     # no winner → a side
])
def test_appeal_compares_outcome_winners(client, sim, before, after, accepted):
    sim.outcome, sim.winner = before
    orig = decided(client)
    sim.outcome, sim.winner = after
    a = wait_status(client, appeal(client, orig["id"]).json()["id"], "decided")
    assert a["appeal_accepted"] is accepted


def test_appeal_when_court_full_is_503_and_can_retry(client, sim):
    orig = decided(client)
    sim.gate.clear()
    first = client.post("/hearing", json=OK).json()["id"]
    wait_status(client, first, "running")
    for _ in range(court.MAX_WAITING):
        client.post("/hearing", json=OK)
    r = appeal(client, orig["id"])
    assert r.status_code == 503 and r.json()["error"] == court.BUSY
    assert client.get(f"/hearing/{orig['id']}").json()["can_appeal"]
    sim.gate.set()


def test_brain_is_stored_data_without_a_sim_call(client, sim):
    hid = decided(client)["id"]
    calls = len(sim.calls)
    for _ in range(3):
        assert client.get(f"/hearing/{hid}/brain").json() == {k: v for k, v in BRAIN.items()
                                                              if k != "taste_hz"}
    assert len(sim.calls) == calls

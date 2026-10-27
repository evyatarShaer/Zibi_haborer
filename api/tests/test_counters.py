"""Share counters (P2B-11): aggregate events per UTC day, one cases_shared per case however
many taps, no case data in the counter table, printed by the admin command."""
import sqlite3

from apikit import as_b, decided, open_case, settled
from borer_api import admin
from borer_api.db import EVENTS
from fake import TEXT_B


def counts(client) -> dict:
    return {r["event"]: r["count"] for r in client.app.state.store.counters()}


def test_one_shared_per_case_however_many_taps(client):
    case = open_case(client)
    r = client.post(f"/api/a/{case['a']}/shared")
    assert r.status_code == 409  # nothing to share before the verdict
    b, _ = decided(client, case)
    firsts = [client.post(f"/api/a/{case['a']}/shared").json()["first"] for _ in range(3)]
    firsts += [b.post(f"/api/b/{case['b']}/shared").json()["first"] for _ in range(3)]
    assert firsts == [True] + [False] * 5
    assert counts(client)["cases_shared"] == 1
    assert client.app.state.store.case(case["case_id"])["shared_at"] is not None


def test_every_event_is_counted(client, clock, sim):
    opened = [open_case(client) for _ in range(3)]
    b, _ = decided(client, opened[0])  # decided
    client.post(f"/api/a/{opened[0]['a']}/appeal")  # appeal
    settled(client, f"/api/a/{opened[0]['a']}", 1)
    client.post(f"/api/c/{opened[0]['case_id']}/report")  # report
    clock.t += 3 * 3600  # opened[1] and [2] are no-shows (also decided)
    for c in opened[1:]:
        settled(client, f"/api/a/{c['a']}", 0)
    assert counts(client) == {"cases_opened": 3, "cases_decided": 3, "no_shows": 2,
                              "appeals": 1, "reports": 1}
    assert len(sim.calls) == 4  # an appeal's verdict is not a new decided case


def test_counter_table_holds_no_case_data(client, tmp_path):
    case = open_case(client)
    b, _ = decided(client, case)
    client.post(f"/api/a/{case['a']}/shared")
    db = sqlite3.connect(tmp_path / "c.sqlite3")
    columns = [r[1] for r in db.execute("PRAGMA table_info(counter)")]
    rows = db.execute("SELECT * FROM counter").fetchall()
    assert columns == ["day", "event", "count"]
    assert {r[1] for r in rows} <= set(EVENTS) and all(isinstance(r[2], int) for r in rows)
    dump = repr(rows)
    assert case["case_id"] not in dump and "דנה" not in dump and TEXT_B not in dump


def test_admin_prints_counters_and_the_exit_share(client, tmp_path, capsys):
    for i in range(2):
        case = open_case(client)
        decided(client, case)
        if i == 0:
            client.post(f"/api/a/{case['a']}/shared")
    assert admin.main(["counters", "--db", str(tmp_path / "c.sqlite3")]) == 0
    out = capsys.readouterr().out
    assert "cases_shared" in out and "shared / decided: 1 / 2 = 50%" in out


def test_busy_appeal_counts_nothing(client, sim):
    case = open_case(client)
    decided(client, case)
    sim.gate.clear()
    for _ in range(4):  # fill the court: 1 running + 3 waiting
        c = open_case(client)
        as_b(client, c).post(f"/api/b/{c['b']}/submit", json={"text_b": TEXT_B})
    assert client.post(f"/api/a/{case['a']}/appeal").status_code == 503
    assert "appeals" not in counts(client)
    sim.gate.set()

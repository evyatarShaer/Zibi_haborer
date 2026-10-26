"""Moderation (P2B-7): the word filter after §4.1 normalization, reports, the admin."""
import pytest

from apikit import as_b, decided, open_case
from borer_api import admin, validate, views, words
from casekit import TEXT_B as CASE_TEXT_B, decided_case, opened
from fake import OK, TEXT_B

LISTED = words.parse(["# a comment", "", "מטומטם", "כוס אמק", "זונה"])


@pytest.fixture
def listed(monkeypatch):
    monkeypatch.setattr(words, "entries", lambda: LISTED)


@pytest.mark.parametrize("text", [
    "אתה מטומטם", "אתה מטומטמ", "אתה מְטוּמְטָם", "והמטומטם הזה", "ﬠ מטומטם",
    "זה כוס אמק אחד", "כוֹס אִמַּק", "בזונה", "  זונה!!"])
def test_listed_words_blocked_after_normalization(text):
    assert words.offensive(text, LISTED)


@pytest.mark.parametrize("text", [
    OK["text_a"], TEXT_B, "תזונה נכונה זה הכי חשוב", "כוס קפה של אמא", "מטומטמים",
    "hello מטו מטם", ""])
def test_clean_text_passes(text):
    assert not words.offensive(text, LISTED)


def test_list_file_and_example_fallback(tmp_path, monkeypatch, caplog):
    assert words.parse(words.EXAMPLE.read_text(encoding="utf-8").splitlines()) == \
        [("מניאק",), ("כוס", "אמק")]
    monkeypatch.setattr(words, "WORDS", tmp_path / "missing.txt")
    words.entries.cache_clear()
    try:
        assert words.entries() == [("מניאק",), ("כוס", "אמק")] and "using" in caplog.text
    finally:
        words.entries.cache_clear()


@pytest.mark.parametrize("field", ["topic", "name_a", "name_b", "text_a"])
def test_open_case_soft_block(client, listed, field):
    value = "מטומטם" if field != "text_a" else "אתה פשוט מטומטם וזהו זה"
    r = client.post("/api/case", json=OK | {field: value})
    assert r.status_code == 422 and r.json()["errors"] == {field: validate.BLOCKED}
    assert client.app.state.store._all('SELECT id FROM "case"') == []


def test_b_argument_soft_block(client, listed, sim):
    case = open_case(client)
    b = as_b(client, case)
    r = b.post(f"/api/b/{case['b']}/submit", json={"text_b": "בעצם כל העניין הזה כוס אמק"})
    assert r.status_code == 422 and r.json()["errors"] == {"text_b": validate.BLOCKED}
    assert not sim.calls and b.get(f"/api/b/{case['b']}").json()["status"] == "waiting"


def test_report_hides_the_whole_case_at_once(client):
    case = open_case(client)
    b, _ = decided(client, case)
    assert client.post(f"/api/c/{case['case_id']}/report").json() == {"hidden": True}
    for r in (client.get(f"/api/c/{case['case_id']}"), client.get(f"/api/a/{case['a']}"),
              b.get(f"/api/b/{case['b']}"), b.get(f"/api/b/{case['b']}/brain/0"),
              client.post(f"/api/c/{case['case_id']}/report")):
        assert r.status_code == 404 and r.json()["error"] == views.CLOSED
    assert client.post("/api/c/nope/report").status_code == 404


def test_hidden_case_gets_no_no_show_hearing(store, clock):
    c = opened(store)
    store.report(c["id"])
    clock.t += 3 * 3600
    assert store.due() == []
    store.restore(c["id"])
    assert store.due() == [c["id"]]


def test_admin_list_restore_delete(store, clock, tmp_path, capsys):
    db = str(tmp_path / "c.sqlite3")
    quiet, loud = opened(store), decided_case(store, clock)
    assert store.report(loud["id"])
    assert admin.main(["list", "--db", db]) == 0
    out = capsys.readouterr().out
    assert loud["id"] in out and quiet["id"] not in out and "reports 1" in out and CASE_TEXT_B in out
    assert admin.main(["restore", loud["id"], "--db", db]) == 0
    assert store.case(loud["id"])["hidden_at"] is None
    assert admin.main(["restore", loud["id"], "--db", db]) == 1  # not hidden any more
    capsys.readouterr()
    admin.main(["list", "--db", db])
    assert loud["id"] in capsys.readouterr().out  # restored: its report stays on record
    assert admin.main(["delete", loud["id"], "--db", db]) == 0
    assert store.case(loud["id"]) is None and store.hearings(loud["id"]) == []
    assert admin.main(["delete", loud["id"], "--db", db]) == 1
    assert admin.main(["list", "--db", str(tmp_path / "nope.sqlite3")]) == 1

"""Determinism checker (borer_api.recheck): a stored hearing equals its rerun field by field."""
from borer_api.cases import Store
from borer_api.recheck import mismatches, stored_hearings
from casekit import CASE, TEXT_B
from fake import FakeSim


def stored(tmp_path, result, text_b=TEXT_B):
    store = Store(str(tmp_path / "c.sqlite3"))
    c = store.open(*CASE, ip="1.2.3.4")
    hid = store.submit_b(c["id"], text_b, 7)
    store.finish(hid, result)
    store.close()
    return stored_hearings(str(tmp_path / "c.sqlite3"))


def test_identical_rerun_has_no_mismatch(tmp_path):
    [row] = stored(tmp_path, FakeSim()("a", "b", 7, 0.0))  # stored mood: the real (tiny) wait
    assert (row["text_a"], row["text_b"], row["n"]) == (CASE[3], TEXT_B, 0)
    assert mismatches(row, FakeSim()(row["text_a"], row["text_b"], row["seed"], row["wait_h"])) == []


def test_changed_rerun_is_reported(tmp_path):
    [row] = stored(tmp_path, FakeSim()("a", "b", 7, 0.0))
    other = FakeSim(outcome="froze")("a", "b", 7, row["wait_h"])
    other["brain"] = {**other["brain"], "mn9_hz": [[0.0], [0.0]]}
    assert mismatches(row, other) == ["metrics", "outcome", "winner", "brain"]

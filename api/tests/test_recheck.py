"""Determinism checker (borer_api.recheck): a stored hearing equals its rerun field by field."""
from borer_api.recheck import mismatches, stored_hearings
from borer_api.store import Store
from fake import OK, FakeSim


def stored(tmp_path, result):
    store = Store(str(tmp_path / "h.sqlite3"))
    hid = store.create(OK["name_a"], OK["name_b"], OK["text_a"], OK["text_b"], 7, result["mood"])
    store.finish(hid, result)
    store.close()
    return stored_hearings(str(tmp_path / "h.sqlite3"))


def test_identical_rerun_has_no_mismatch(tmp_path):
    result = FakeSim()("a", "b", 7)
    [row] = stored(tmp_path, result)
    assert mismatches(row, result) == []


def test_changed_rerun_is_reported(tmp_path):
    result = FakeSim()("a", "b", 7)
    [row] = stored(tmp_path, result)
    other = FakeSim(outcome="froze")("a", "b", 7)
    other["brain"] = {**other["brain"], "mn9_hz": [[0.0], [0.0]]}
    assert mismatches(row, other) == ["metrics", "outcome", "winner", "brain"]

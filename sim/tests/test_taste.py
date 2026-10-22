"""borer_sim.taste: SPEC §4 text → GRN drive."""
import pytest

from borer_sim import taste
from borer_sim.params import TASTE

SENTENCE = "אתה תמיד שוכח לסגור את הדלת, וזה ממש מעצבן אותי"
R_BASE = TASTE["r_base"]
MARKS = (taste.EXCLAMATION, taste.QUESTION)


def _letters_excess(rates) -> float:
    return sum((rates[l] - R_BASE) * taste._n(l) for l in taste.LETTERS)


def test_normalize_niqqud_finals_spaces():
    assert taste.normalize("שָׁלוֹם") == "שלומ"
    assert taste.normalize("ךםןףץ") == "כמנפצ"
    assert taste.normalize("  אב \n\t  גד  ") == "אב גד"


def test_normalize_caps_length():
    assert len(taste.normalize("א" * 500)) == TASTE["max_chars"]


def test_no_letters_is_plain_water():
    rates = taste.letter_rates("abc 123")
    assert all(rates[l] == R_BASE for l in taste.LETTERS)


@pytest.mark.needs_data
def test_letters_total_drive_fixed_by_length():
    for text in (SENTENCE, "ד" * 47, "דב" * 23 + "ק"):
        target = taste._reference_total() * taste.length_gain(len(taste.normalize(text)))
        assert _letters_excess(taste.letter_rates(text)) == pytest.approx(target, rel=1e-12)


@pytest.mark.needs_data
@pytest.mark.xfail(strict=True, reason="v4 fixed total undoes saturation: 280 x ד drives "
                   "PhG1c at ~6 kHz/GRN (SPEC §4.6 violated; open, DECISIONS.md 2026-10-22)")
def test_spamming_one_letter_saturates():
    cap = R_BASE + taste.length_gain(280) * TASTE["r_max"]
    assert taste.letter_rates("ד" * 280)["ד"] <= cap


@pytest.mark.parametrize("mark", MARKS)
def test_punctuation_capped(mark):
    assert taste.letter_rates("כן")[mark] == R_BASE
    one = taste.letter_rates("כן" + mark)[mark]
    flood = taste.letter_rates(mark * 280)[mark]
    assert R_BASE < one < flood <= R_BASE + TASTE["punct_max"]


def test_too_long_turns_aversive():
    assert taste.letter_rates(SENTENCE)["!"] == R_BASE
    assert taste.letter_rates(SENTENCE * 6)["!"] > R_BASE


@pytest.mark.needs_data
def test_left_right_total_drive_equal():
    left, right = taste.drives(SENTENCE, "left"), taste.drives(SENTENCE, "right")
    assert len(left) == len(taste.TABLE)
    for (li, lr), (ri, rr) in zip(left, right):
        assert li and ri and set(li).isdisjoint(ri)
        assert lr * len(li) == pytest.approx(rr * len(ri), rel=1e-12)
    assert taste.tasting(SENTENCE) == left + right


@pytest.mark.needs_data
def test_deterministic_and_bad_side():
    assert taste.drives(SENTENCE, "left") == taste.drives(SENTENCE, "left")
    with pytest.raises(ValueError):
        taste.drives(SENTENCE, "center")


def test_table_covers_letters_and_marks():
    assert set(taste.TABLE) == set(taste.LETTERS) | set(MARKS)
    assert len(taste.LETTERS) == 22 and set(taste.CHAT_FREQ) == set(taste.LETTERS)
    assert sum(taste.CHAT_FREQ.values()) == pytest.approx(1, abs=1e-3)
    names = [g for g, _ in taste.TABLE.values()]
    assert len(set(names)) == len(names) and not set(names) & taste.EXCLUDED
    assert all(taste.TABLE[l][1][0] == "E" for l in "דבש")  # honey
    assert all(taste.TABLE[m][1][0] == "I" for m in MARKS)


@pytest.mark.needs_data
def test_table_groups_exist_with_grns_on_both_sides():
    for key in taste.TABLE:
        assert all(len(v) >= taste.MIN_PER_SIDE for v in taste._side_indices(key).values())

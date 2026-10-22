"""borer_sim.taste: SPEC §4 text → GRN drive."""
from collections import Counter

import pytest

from borer_sim import taste
from borer_sim.params import TASTE
from validation.taste_spam import SILENCE, SPAM

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


@pytest.mark.parametrize("text", SILENCE.values())
def test_no_hebrew_is_baseline_only(text):
    assert set(taste.letter_rates(text).values()) == {R_BASE}


@pytest.mark.needs_data
def test_natural_letters_total_drive_fixed_by_length():
    """A natural text (coverage >= coverage_ref, no rate at the cap) keeps the fixed total."""
    rates = taste.letter_rates(SENTENCE)
    assert taste.coverage(Counter(taste.normalize(SENTENCE))) >= TASTE["coverage_ref"]
    assert max(rates[l] for l in taste.LETTERS) < TASTE["cap"]
    target = taste._reference_total() * taste.length_gain(len(taste.normalize(SENTENCE)))
    assert _letters_excess(rates) == pytest.approx(target, rel=1e-12)


@pytest.mark.needs_data
def test_spamming_one_letter_saturates():
    """Repeating a letter adds no drive: its rate stays at the coverage-scaled cap."""
    cap_excess = TASTE["cap"] - R_BASE
    for l in taste.LETTERS:
        f = (taste.CHAT_FREQ[l] / TASTE["coverage_ref"]) ** TASTE["coverage_power"]
        rates = [taste.letter_rates(l * n)[l] for n in (10, 50, 140, 280)]
        assert rates == pytest.approx([R_BASE + cap_excess * f] * 4, rel=1e-12)


@pytest.mark.needs_data
@pytest.mark.parametrize("name", SPAM)
def test_spam_drive_below_natural(name):
    """Every spam text: no rate above the cap, letters' drive well below a natural text's."""
    rates = taste.letter_rates(SPAM[name])
    assert max(rates[l] for l in taste.LETTERS) <= TASTE["cap"]
    assert _letters_excess(rates) < 0.15 * _letters_excess(taste.letter_rates(SENTENCE))


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

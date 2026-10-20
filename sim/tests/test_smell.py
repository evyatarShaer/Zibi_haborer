"""borer_sim.smell: SPEC §4 text → ORN drive."""
import pytest

from borer_sim import anatomy, smell
from borer_sim.params import SMELL

# Hebrew letter frequencies, finals merged: Rabinovich & Wintner (2016),
# "Frequencies of letter n-grams in Hebrew and Arabic", Univ. of Haifa —
# 12 M words of HaAretz (1991). See DECISIONS.md 2026-10-20 (P1-6).
HEBREW_FREQ = {
    "א": 0.04822, "ב": 0.05207, "ג": 0.01443, "ד": 0.02665, "ה": 0.08776,
    "ו": 0.10912, "ז": 0.00862, "ח": 0.02446, "ט": 0.01328, "י": 0.11855,
    "כ": 0.02631, "ל": 0.06659, "מ": 0.08312, "נ": 0.04675, "ס": 0.01743,
    "ע": 0.03223, "פ": 0.02291, "צ": 0.01494, "ק": 0.02330, "ר": 0.05811,
    "ש": 0.04785, "ת": 0.05730,
}
PALP = {"VA4", "VA7l", "VC1", "VC2", "VM7d", "VM7v"}
SENTENCE = "אתה תמיד שוכח לסגור את הדלת, וזה ממש מעצבן אותי"
R_BASE = SMELL["r_base"]


def test_normalize_niqqud_finals_spaces():
    assert smell.normalize("שָׁלוֹם") == "שלומ"
    assert smell.normalize("ךםןףץ") == "כמנפצ"
    assert smell.normalize("  אב \n\t  גד  ") == "אב גד"


def test_normalize_caps_length():
    assert len(smell.normalize("א" * 500)) == SMELL["max_chars"]


def test_spamming_one_letter_saturates():
    spam = smell.glomerulus_rates("ד" * 280)
    half = smell.glomerulus_rates("דב" * 140)
    assert spam["DM1"] < 1.06 * half["DM1"]  # doubling the share adds < 6 %
    assert spam["DM1"] < R_BASE + smell.length_gain(280) * SMELL["r_max"]
    assert sum(spam.values()) < sum(smell.glomerulus_rates(SENTENCE).values())


@pytest.mark.parametrize("mark,glom", [smell.EXCLAMATION, smell.QUESTION])
def test_punctuation_capped(mark, glom):
    assert smell.glomerulus_rates("כן")[glom] == R_BASE
    one = smell.glomerulus_rates("כן" + mark)[glom]
    flood = smell.glomerulus_rates(mark * 280)[glom]
    assert R_BASE < one < flood <= R_BASE + SMELL["punct_max"]


def test_too_long_turns_aversive():
    v = smell.EXCLAMATION[1]
    assert smell.glomerulus_rates(SENTENCE)[v] == R_BASE
    assert smell.glomerulus_rates(SENTENCE * 6)[v] > R_BASE


@pytest.mark.needs_data
def test_left_right_total_drive_equal():
    left, right = smell.drives(SENTENCE, "left"), smell.drives(SENTENCE, "right")
    for (li, lr), (ri, rr) in zip(left, right):
        assert set(li).isdisjoint(ri)
        assert lr * len(li) == pytest.approx(rr * len(ri), rel=1e-12)


@pytest.mark.needs_data
def test_deterministic_and_bad_side():
    assert smell.drives(SENTENCE, "left") == smell.drives(SENTENCE, "left")
    with pytest.raises(ValueError):
        smell.drives(SENTENCE, "center")


def test_table_frequency_balance():
    assert set(smell.LETTERS) == set(HEBREW_FREQ)
    total = {v: sum(HEBREW_FREQ[l] for l, (_, val) in smell.LETTERS.items() if val == v)
             for v in (smell.ATTRACTIVE, smell.AVERSIVE, smell.NEUTRAL)}
    a, v = total[smell.ATTRACTIVE], total[smell.AVERSIVE]
    assert abs(a - v) <= 0.10 * (a + v) / 2
    counts = [sum(val == g for _, val in smell.LETTERS.values()) for g in total]
    assert counts == [7, 7, 8]
    assert all(smell.LETTERS[l][1] == smell.ATTRACTIVE for l in "דבש")  # honey


@pytest.mark.needs_data
def test_table_glomeruli_antennal_distinct_and_sized():
    gloms = [g for g, _ in smell.LETTERS.values()]
    assert len(set(gloms)) == 22
    assert not set(gloms) & (PALP | {"V", "DA2"})
    t = anatomy.orn_glomeruli()
    for g in gloms + ["V", "DA2"]:
        assert t.loc[g, "nerve"] == "AN"
        assert min(t.loc[g, "left"], t.loc[g, "right"]) >= 5

"""Input rules of a case (SPEC §3, §14.1), with Hebrew messages for the page."""
from borer_sim.argument import MIN_LETTERS, hebrew_letters
from borer_sim.params import TASTE

MAX_TEXT, MAX_NAME, MAX_TOPIC = TASTE["max_chars"], 30, 80
SIDES = {"a": "א׳", "b": "ב׳"}


def problems(topic: str | None, names: dict, texts: dict) -> dict[str, str]:
    """{field: Hebrew message} for each invalid field; empty when all are fine.
    names / texts: {"a": ..., "b": ...} for the sides being checked, already stripped."""
    out = {}
    if topic and len(topic) > MAX_TOPIC:
        out["topic"] = f"נושא התיק ארוך מדי (עד {MAX_TOPIC} תווים)"
    for s, name in names.items():
        if not name:
            out[f"name_{s}"] = f"חסר שם לצד {SIDES[s]}"
        elif len(name) > MAX_NAME:
            out[f"name_{s}"] = f"השם של צד {SIDES[s]} ארוך מדי (עד {MAX_NAME} תווים)"
    for s, text in texts.items():
        n = hebrew_letters(text)
        if len(text) > MAX_TEXT:
            out[f"text_{s}"] = f"הטענה של צד {SIDES[s]} ארוכה מדי (עד {MAX_TEXT} תווים)"
        elif n < MIN_LETTERS:
            out[f"text_{s}"] = (f"הטענה של צד {SIDES[s]} צריכה לפחות {MIN_LETTERS} אותיות "
                                f"בעברית (יש {n})")
    return out

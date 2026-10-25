"""Input rules of a new hearing (SPEC §3, §14.1), with Hebrew messages for the page."""
from borer_sim.argument import MIN_LETTERS, hebrew_letters
from borer_sim.params import TASTE

MAX_TEXT, MAX_NAME, MAX_TOPIC = TASTE["max_chars"], 30, 80
SIDES = {"a": "א׳", "b": "ב׳"}


def problems(topic: str | None, names: dict, texts: dict) -> dict[str, str]:
    """{field: Hebrew message} for each invalid field; empty when the hearing can run.
    names / texts: {"a": ..., "b": ...}, already stripped."""
    out = {}
    if topic and len(topic) > MAX_TOPIC:
        out["topic"] = f"נושא התיק ארוך מדי (עד {MAX_TOPIC} תווים)"
    for s, label in SIDES.items():
        if not names[s]:
            out[f"name_{s}"] = f"חסר שם לצד {label}"
        elif len(names[s]) > MAX_NAME:
            out[f"name_{s}"] = f"השם של צד {label} ארוך מדי (עד {MAX_NAME} תווים)"
        n = hebrew_letters(texts[s])
        if len(texts[s]) > MAX_TEXT:
            out[f"text_{s}"] = f"הטענה של צד {label} ארוכה מדי (עד {MAX_TEXT} תווים)"
        elif n < MIN_LETTERS:
            out[f"text_{s}"] = (f"הטענה של צד {label} צריכה לפחות {MIN_LETTERS} אותיות "
                                f"בעברית (יש {n})")
    return out

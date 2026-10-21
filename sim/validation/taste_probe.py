"""Taste each argument alone; the one the fly wants to eat more wins (probe).

Run from sim/:
    PYTHONPATH=src uv run python -m validation.taste_probe screen
    PYTHONPATH=src uv run python -m validation.taste_probe tastings
Validation only: no change to SPEC, model.py or smell.py. ARGUMENTS are
hand-written test data (typical WhatsApp disputes), not product text.
"""
import random
import sys
from itertools import combinations

from borer_sim import data
from validation import steering, taste
from validation.readout_probe import pop_metrics
from validation.steering_probe import THREADS, WORKERS
from validation.sugar_mn9 import OUT

ARGUMENTS = [
    "אתה תמיד מאחר, וזה כבר לא מצחיק.",
    "מי שבישל לא שוטף כלים, זה החוק בבית הזה!",
    "ביקשתי שתקנה חלב, למה שכחת שוב??",
    "פיצה עם אננס זה פשוט טעים ונקודה.",
    "אין מצב שאני משלם על המונית, אתה הזמנת אותה!",
    "הכלב שלך נבח כל הלילה ואף אחד בבניין לא ישן.",
    "תודה רבה על העזרה עם המעבר, באמת, אבל זה עדיין היה התור שלך לנקות את המטבח"
    " ואת הסלון, ואני לא מתכוון לעשות את זה במקומך שוב.",
    "למה אתה תמיד מחליט לבד איפה אוכלים בשישי?",
    "המזגן על 18 מעלות זה פשוט קפוא, תעלה ל-24.",
    "אמרת שתחזיר את הכסף ביום ראשון, היום כבר חמישי!!",
    "אני לא צועקת, אני רק מדברת בקול רם כי כבר שעה אני מנסה להסביר לך משהו פשוט"
    " ואתה ממשיך להסתכל בטלפון.",
    "הסדרה הזאת משעממת, בוא נראה משהו אחר.",
    "החניה הזאת שלי, אני משלם עליה כל חודש מאתיים וחמישים שקל, ושלוש פעמים השבוע"
    " מצאתי בה את האוטו שלך. בפעם הבאה אני מזמין גרר ולא מתנצל על זה, ואל תגיד"
    " שלא הזהרתי אותך מראש!",
    "מי השאיר את הדלת של המקרר פתוחה כל הבוקר?",
    "עדיף לטוס לאילת בחורף, בקיץ זה גיהנום.",
    "ההורים שלך באים אלינו כל שבת כבר שלושה חודשים, ואני מבקש שלפחות פעם בחודש"
    " נהיה לבד בבית.",
    "דבש בתה זה הכי טוב בעולם, סוכר זה לחלשים.",
    "קנית את הכרטיסים בלי לשאול אותי? באמת?",
    "הילדים צריכים ללכת לישון בשמונה ולא בעשר, הם קמים עייפים ומאחרים לגן."
    " זה לא נתון לוויכוח!",
    "בפעם הבאה אני בוחר את המסעדה, בפעם הקודמת היה נורא!",
]
PAIRS = random.Random(783).sample(list(combinations(range(len(ARGUMENTS)), 2)), 30)
SEEDS = tuple(range(783, 793))
SCREEN_RATE, SCREEN_SEEDS = 150.0, (783, 784, 785)
DURATION_MS, ARGS_FILE = 2000, "taste_args_2s.jsonl"  # rerun; 1 s results: taste_args.jsonl
assert all(30 <= len(a) <= 200 for a in ARGUMENTS), [len(a) for a in ARGUMENTS]


def tasting(text: str):
    """One tasting: the argument on both sides of the labellum at once."""
    return taste.drives(text, "left") + taste.drives(text, "right")


def run(name, jobs, duration_ms=1000):
    print(f"{name}: {len(jobs)} jobs", flush=True)
    return steering.run_jobs(jobs, OUT / name, WORKERS, THREADS, metric=pop_metrics,
                             duration_ms=duration_ms)


def screen():
    """Every eligible GRN group alone, both sides, at SCREEN_RATE Hz per GRN."""
    groups = taste._groups(taste.grns())
    run("taste_screen.jsonl", {
        f"{name}|{seed}": ([(data.to_index(ids), SCREEN_RATE)], seed)
        for name, _, ids in groups for seed in SCREEN_SEEDS})


def tastings():
    for key, (name, ids) in taste.mapping().items():
        print(f"  {key} -> {name} ({len(ids)} GRNs)")
    run(ARGS_FILE, {f"{i}|{seed}": (tasting(a), seed)
                    for i, a in enumerate(ARGUMENTS) for seed in SEEDS}, DURATION_MS)


if __name__ == "__main__":
    {"screen": screen, "tastings": tastings}[sys.argv[1]]()

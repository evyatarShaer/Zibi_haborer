// User-facing Hebrew text. Verdict headlines are SPEC §7 (decided 2026-10-25); the mood
// and waiting lines are placeholder copy for the owner to replace.
export const T = {
  title: "הבורר",
  tagline: "שני צדדים, טענה אחת לכל צד, זבוב אחד שמכריע",
  topic: "על מה הוויכוח? (לא חובה)",
  topicHint: "הזבוב לא טועם את הנושא, הוא רק יופיע בפסק הדין",
  side: { a: "צד א׳", b: "צד ב׳" },
  name: "שם",
  argument: "הטענה",
  submit: "לבית המשפט!",
  letters: (n, min) => `${n}/${min} אותיות בעברית`,
  chars: (n, max) => `${n}/${max} תווים`,
  sending: "מגישים את התיק…",
  noConnection: "אין חיבור לשרת. נסו שוב",
  queued: "התיק ממתין בתור. השופט מסיים דיון אחר…",
  enters: "השופט נכנס לאולם",
  entersAppeal: "ערעור! השופט חוזר לאולם",
  tasting: (name) => `טועם את הטענה של ${name}…`,
  deliberating: ["השופט מתלבט…", "שוקל את הטעמים…", "עוד רגע ההכרעה…"],
  failed: "משהו השתבש בדיון. אפשר לנסות שוב",
  retry: "לנסות שוב",
  notFound: "התיק לא נמצא (אולי עברו 7 ימים והוא נמחק)",
  appetite: "תיאבון",
  newArgument: "ויכוח חדש",
  appeal: "ערעור",
  appealing: "מגישים ערעור…",
  toAppeal: "לתוצאת הערעור",
  appealAccepted: "הערעור התקבל!",
  appealRejected: "הערעור נדחה. הפסק סופי",
  brain: "מה קרה במוח?",
  brainHide: "הסתר את המוח",
  brainLoading: "פותחים את המוח…",
};

const HUNGER = [[0.25, "שבע"], [0.5, "קצת רעב"], [0.8, "רעב"], [Infinity, "מורעב"]];
const MOOD = [[0.15, "רגוע"], [0.3, "קצת עצבני"], [Infinity, "עצבני"]];
const pick = (scale, x) => scale.find(([top]) => x < top)[1];

export function moodLine(m) {
  return `מצב השופט היום: ${pick(HUNGER, m.hunger)}, ${pick(MOOD, m.arousal)}.`;
}

export function topicLine(h) {
  return h.topic ? `התיק: ${h.topic}` : null;
}

export function headline(h) {
  return {
    win: `פסק הדין: הצדק עם ${h.winner_name}`,
    dithered: `אחרי התלבטות קשה... הצדק עם ${h.winner_name}`,
    tie: "תיקו. הזבוב לא השתכנע מאף אחד",
    froze: "הזבוב קפא. התיק הזה גדול עליו",
    food: "הבורר יצא להפסקת צהריים. הדיון נדחה",
  }[h.outcome];
}

// The lab view (SPEC §15.7): MN9 curves and the run's identity; no taste classes.
export const LAB = {
  title: "מה קרה במוח?",
  noAi: "140 אלף נוירונים של מוח זבוב אמיתי. בלי AI.",
  mn9: "נוירון הבליעה (MN9)",
  mn9Hint: "קצב הירי בזמן הטעימה (הרץ), ממוצע נע של רבע שנייה",
  at: (s, parts) => `${s.toFixed(2)} ש׳ · ${parts.join(" · ")}`,
  hz: (x) => `${Math.round(x)} הרץ`,
  seconds: "ש׳",
  judge: "מצב השופט",
  hunger: "רעב",
  irritability: "עצבנות",
  seed: "זרע אקראי",
  version: "גרסת סימולציה",
  platform: "מחשב",
  error: "לא הצלחנו לפתוח את המוח. נסו שוב",
};

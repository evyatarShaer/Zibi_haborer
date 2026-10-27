// User-facing Hebrew text. Verdict headlines and the history line come from the API
// (borer_api.verdicts); the rest is placeholder copy for the owner to replace.
export const T = {
  title: "הבורר",
  tagline: "פותחים תיק, שולחים לצד השני, זבוב אחד מכריע",
  topic: "על מה הוויכוח? (לא חובה)",
  topicHint: "הזבוב לא טועם את הנושא, הוא רק יופיע בפסק הדין",
  yourName: "השם שלך",
  otherName: "השם של הצד השני",
  yourArgument: "הטענה שלך",
  argumentPlaceholder: "למה אני צודק/ת…",
  blindHint: "הצד השני לא יראה את הטענה שלך לפני שיגיש את שלו",
  blindHintB: (a) => `את הטענה של ${a} תראו רק אחרי שתגישו את שלכם`,
  open: "לפתוח תיק",
  opening: "פותחים את התיק…",
  letters: (n, min) => `${n}/${min} אותיות בעברית`,
  chars: (n, max) => `${n}/${max} תווים`,
  noConnection: "אין חיבור לשרת. נסו שוב",
  failed: "משהו השתבש. נסו שוב",
  personal: "הקישור הזה אישי. אל תשתפו אותו, שתפו רק את פסק הדין",
  // A waits for B (SPEC §3.2)
  waitingFor: (name) => `בית המשפט ממתין לטענה של ${name}`,
  timeLeft: (t) => `נשארו ${t} שעות להגשה`,
  sendToB: "לשלוח לצד השני בוואטסאפ",
  nudgeB: "להציק שוב בוואטסאפ",
  invite: (a, topic, url) => `${a} פתח/ה נגדך תיק בבית המשפט של הזבוב${topic ? `: ${topic}` : ""}. ` +
    `יש לך 3 שעות להגיש טענה. הזבוב מחכה: ${url}`,
  nudgeText: (a, left, url) => `הזבוב עדיין מחכה לטענה שלך בתיק של ${a}. נשארו ${left} שעות: ${url}`,
  // B writes blind (SPEC §15.2)
  summoned: (a) => `${a} פתח/ה נגדך תיק`,
  submitB: "להגיש לזבוב",
  submitting: "מגישים…",
  // the story (SPEC §14.3)
  queued: "התיק ממתין בתור. השופט מסיים דיון אחר…",
  enters: "השופט נכנס לאולם",
  entersAppeal: (name) => `ערעור של ${name}! השופט חוזר לאולם`,
  tasting: (name) => `טועם את הטענה של ${name}…`,
  tastingWater: "הצד השני לא הגיע. טועם כוס מים…",
  deliberating: ["השופט מתלבט…", "שוקל את הטעמים…", "עוד רגע ההכרעה…"],
  hungry: (h) => `הזבוב רעב כבר ${h} שעות.`,
  revealing: "כמה הזבוב רצה לבלוע כל טענה…",
  // the verdict (SPEC §7, §8, §15.4)
  water: "כוס מים",
  appetite: "תיאבון",
  appealAcceptedBy: (name) => `הערעור של ${name} התקבל!`,
  appealRejectedBy: (name) => `הערעור של ${name} נדחה`,
  final: "הפסק סופי",
  appeal: "ערעור",
  appealing: "מגישים ערעור…",
  appealLeft: (t) => `אפשר לערער עוד ${t} שעות`,
  shareVerdict: "לשלוח את פסק הדין",
  shareText: (topic, head, url) => `${topic ? `התיק: ${topic}\n` : ""}${head}\n${url}`,
  newCase: "לפתוח תיק חדש",
  // closed / taken / public card (SPEC §9, §15.5, §15.8)
  closed: "התיק נסגר. אפשר לפתוח תיק חדש",
  ownLink: "זה הקישור של הצד השני. שלחו אותו אליו",
  taken: "התיק כבר בטיפול",
  notDecided: "הזבוב עוד לא פסק בתיק הזה",
  report: "דיווח על תוכן פוגעני",
  reportSure: "בטוח? לחצו שוב כדי להסתיר את התיק",
  brain: "מה קרה במוח?",
  brainHide: "הסתר את המוח",
  brainLoading: "פותחים את המוח…",
  how: "איך זה עובד?",
};

const HUNGER = [[0.25, "שבע"], [0.5, "קצת רעב"], [0.8, "רעב"], [Infinity, "מורעב"]];
const MOOD = [[0.15, "רגוע"], [0.3, "קצת עצבני"], [Infinity, "עצבני"]];
const pick = (scale, x) => scale.find(([top]) => x < top)[1];

// The story's mood line; `waitH` (hours B took, 3 for a no-show) adds the hunger line
// from half an hour (SPEC §5: "the fly has been hungry for 3 hours").
export function moodLine(m, waitH) {
  const line = `מצב השופט היום: ${pick(HUNGER, m.hunger)}, ${pick(MOOD, m.arousal)}.`;
  return waitH >= 0.5 ? `${line} ${T.hungry((Math.round(waitH * 2) / 2).toString())}` : line;
}

export function topicLine(c) {
  return c.topic ? `התיק: ${c.topic}` : null;
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

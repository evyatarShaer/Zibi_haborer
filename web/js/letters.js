// What the fly will taste (SPEC §3, §4.1), for the live counter: a mirror of
// borer_sim.taste.normalize and borer_sim.argument, tested against Python
// (api/tests/test_web.py). Lengths count code points, as Python does.
export const MIN_LETTERS = 10;
export const MAX_CHARS = 280;
const LETTERS = "אבגדהוזחטיכלמנסעפצקרשת";
const FINALS = { "ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ" };

export function normalize(text) {
  const t = text.normalize("NFKD").replace(/\p{Mn}/gu, "").replace(/\s+/g, " ").trim()
    .replace(/[ךםןףץ]/g, (c) => FINALS[c]);
  return Array.from(t).slice(0, MAX_CHARS).join("");
}

export function hebrewLetters(text) {
  return Array.from(normalize(text)).filter((c) => LETTERS.includes(c)).length;
}

export function chars(text) {
  return Array.from(text.trim()).length;
}

export function argumentOk(text) {
  return hebrewLetters(text) >= MIN_LETTERS && chars(text) <= MAX_CHARS;
}

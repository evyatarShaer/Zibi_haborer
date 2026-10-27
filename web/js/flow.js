// The case flow's pure logic (SPEC §3, §9, §15), tested in Node: which screen a personal
// page shows, the appeal line, the WhatsApp links and the countdowns. Headlines and the
// history line come from the API (borer_api.verdicts). No DOM here.
import { T } from "./copy.js";

export const last = (view) => view.hearings[view.hearings.length - 1];

// The screen for a personal page. `seen`: the highest hearing n this device has already
// shown (-1 for none). A hearing still running is watched live; a decided one this
// device has not seen is replayed from stored data; otherwise the verdict.
export function screen(view, seen) {
  if (view.status === "error") return { kind: "error" };
  if (view.status === "waiting") return { kind: view.you === "A" ? "waitA" : "writeB" };
  const h = last(view);
  if (h.status !== "decided") return { kind: "story", n: h.n };
  if (seen < h.n) return { kind: "story", n: h.n };
  return { kind: "verdict", n: h.n };
}

// "An appeal is accepted if its winner differs from the previous verdict's" (API field).
export function appealLine(view, h) {
  if (h.n === 0) return null;
  const who = h.appealed_by === "A" ? view.name_a : view.name_b;
  return h.accepted ? T.appealAcceptedBy(who) : T.appealRejectedBy(who);
}

// h:mm, rounded up to the minute (never shows 0:00 while time is left).
export function clock(seconds) {
  const m = Math.max(0, Math.ceil(seconds / 60));
  return `${Math.floor(m / 60)}:${String(m % 60).padStart(2, "0")}`;
}

export const waLink = (text) => `https://wa.me/?text=${encodeURIComponent(text)}`;
export const invite = (view, url) => waLink(T.invite(view.name_a, view.topic, url));
export const nudge = (view, url) => waLink(T.nudgeText(view.name_a, clock(view.deadline_in_s), url));
export const shareVerdict = (view, h, url) =>
  waLink(T.shareText(view.topic, h.headline, url));

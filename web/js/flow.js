// The case flow's pure logic (SPEC §3, §8, §9, §15), tested in Node: which screen a
// personal page shows, verdict headlines (no-show included), the history line, the
// WhatsApp links and the countdowns. No DOM here.
import { T, headline } from "./copy.js";

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

// SPEC §8: a no-show has its own headlines, "the fly preferred water" when water wins.
export function verdictHeadline(view, h) {
  if (view.no_show) return h.winner === "B" ? T.preferredWater : T.noShow;
  return headline(h);
}

// "An appeal is accepted if its winner differs from the previous verdict's" (API field).
export function appealLine(view, h) {
  if (h.n === 0) return null;
  const who = h.appealed_by === "A" ? view.name_a : view.name_b;
  return h.accepted ? T.appealAcceptedBy(who) : T.appealRejectedBy(who);
}

// verdict → appeal accepted → appeal rejected (decided hearings only).
export function historyLine(view) {
  const steps = view.hearings.filter((h) => h.status === "decided")
    .map((h) => (h.n === 0 ? T.historyVerdict : h.accepted ? T.historyAccepted : T.historyRejected));
  return steps.length > 1 ? steps.join(" ← ") : null;
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
  waLink(T.shareText(view.topic, verdictHeadline(view, h), url));

// The judge fly (DECISIONS 2026-10-29): one SVG per pose in /img/fly/ (drawn by
// scripts/make_fly.py; any file can be swapped for the owner's art under the same name).
// Which pose each story stage, outcome and notice shows; pure parts tested in Node.
import { el } from "./dom.js";

// Same as OG pose table in api/src/borer_api/og.py (POSE).
export const OUTCOME_POSE = { win: "gavel", dithered: "gavel", tie: "shrug", froze: "frozen", food: "eating" };
const STAGE_POSE = { queued: "seated", mood: "seated", tasteA: "tasting", tasteB: "tasting",
  deliberate: "deliberating", reveal: "deliberating" };
const NOTICE_POSE = { error: "fainted", closed: "asleep" };

export const outcomePose = (outcome) => OUTCOME_POSE[outcome] || "seated";
export const stagePose = (key) => STAGE_POSE[key] || "seated";
export const noticePose = (kind) => NOTICE_POSE[kind] || "seated";

export const flyImg = (pose, size = 124) =>
  el("img", { class: "judge", src: `/img/fly/${pose}.svg`, alt: "", width: size, height: size, "data-pose": pose });

// Change the pose of a fly already on screen (the story), only when it differs.
export function setPose(img, pose) {
  if (img.dataset.pose === pose) return;
  img.dataset.pose = pose;
  img.src = `/img/fly/${pose}.svg`;
}

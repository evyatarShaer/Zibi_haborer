// One-message pages (SPEC §15.1, §15.8): case closed, B's link taken by another device,
// A's own device on B's link, a case that ended in error; each with "open a new case".
// Also the skeleton a case page shows until its first answer.
import { el, show } from "./dom.js";
import { T } from "./copy.js";
import { flyImg, noticePose } from "./fly.js";
import { withIcon } from "./icons.js";

export function noticeScreen(root, message, kind) {
  show(root, el("section", { class: `card waiting notice notice-${kind}` },
    flyImg(noticePose(kind)),
    el("p", { class: "stage-title" }, message),
    el("a", { class: "button primary", href: "/" }, withIcon("plus", T.newCase))));
  return { update: () => {}, stop: () => {} };
}

export function loadingScreen(root) {
  show(root, el("section", { class: "card skeleton", "aria-busy": "true", "aria-label": T.loading },
    el("i", { class: "round" }), el("i", { class: "w60" }), el("i", { class: "w80" }), el("i", { class: "tall" }),
    el("i", { class: "tall" })));
}

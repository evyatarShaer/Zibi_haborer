// One-message pages (SPEC §15.1, §15.8): case closed, B's link taken by another device,
// A's own device on B's link, a case that ended in error; each with "open a new case".
import { el, show } from "./dom.js";
import { T } from "./copy.js";

export function noticeScreen(root, message, kind) {
  show(root, el("section", { class: `card waiting notice notice-${kind}` },
    el("div", { class: "judge", "aria-hidden": "true" }, "🪰"),
    el("p", { class: "stage-title" }, message),
    el("a", { class: "button primary", href: "/" }, T.newCase)));
  return { update: () => {}, stop: () => {} };
}

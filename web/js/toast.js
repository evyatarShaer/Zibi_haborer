// Toasts (DECISIONS 2026-10-29): one short message at a time above the bottom edge, for
// transient events (appeal filed, WhatsApp opening, connection lost / back). Form errors
// stay inline under their fields.
import { el } from "./dom.js";
import { icon } from "./icons.js";

const ICON = { ok: "check", error: "wifiOff", info: "whatsapp" };
let region = null;

export function toast(text, kind = "ok", ms = 3200) {
  if (!region) {
    region = el("div", { class: "toasts", role: "status", "aria-live": "polite" });
    document.body.append(region);
  }
  const t = el("div", { class: `toast toast-${kind}` }, icon(ICON[kind] || "check"), el("span", {}, text));
  region.replaceChildren(t);
  requestAnimationFrame(() => requestAnimationFrame(() => t.classList.add("in")));
  setTimeout(() => {
    t.classList.remove("in");
    setTimeout(() => t.remove(), 300);
  }, ms);
}

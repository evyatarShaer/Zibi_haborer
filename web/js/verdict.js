// Verdict screen (SPEC §7, §14.4–6, P2A-6/7/8): on an appeal, its result line first; the
// "התיק:" line when there is a topic; the outcome headline; an appetite meter per side
// (A, B MN9 rate); then new argument, appeal (original hearings only, once) and the brain view.
import { el, show } from "./dom.js";
import { postAppeal } from "./api.js";
import { T, headline, topicLine } from "./copy.js";
import { brainToggle } from "./brain.js";

// Pure (tested in Node): what the screen shows for a decided hearing.
export function verdictModel(h) {
  const { A, B } = h.appetite;
  const top = Math.max(A, B), sum = A + B;
  const meter = (s, name, text, rate) => ({
    name, text, winner: h.winner === s,
    share: sum > 0 ? Math.round((100 * rate) / sum) : 0,
    width: top > 0 ? Math.round((100 * rate) / top) : 0,
  });
  const appeal = h.appeal_accepted === true ? T.appealAccepted
    : h.appeal_accepted === false ? T.appealRejected : null;
  return { appeal, topic: topicLine(h), headline: headline(h), outcome: h.outcome,
    canAppeal: Boolean(h.can_appeal), appealId: h.appeal_id || null,
    meters: [meter("A", h.name_a, h.text_a, A), meter("B", h.name_b, h.text_b, B)] };
}

function meterNode(m) {
  return el("div", { class: `meter${m.winner ? " winner" : ""}` },
    el("div", { class: "meter-head" }, el("strong", {}, m.name), el("span", {}, `${T.appetite} ${m.share}%`)),
    el("div", { class: "bar", role: "img", "aria-label": `${T.appetite} ${m.share}%` },
      el("div", { class: "fill", style: `width: ${m.width}%` })),
    el("p", { class: "argument" }, `“${m.text}”`));
}

// The appeal button: files the appeal, then hands its id to onAppealed (the waiting story).
function appealButton(h, onAppealed) {
  const message = el("p", { class: "error", "aria-live": "polite" });
  const button = el("button", { class: "secondary" }, T.appeal);
  button.addEventListener("click", async () => {
    button.disabled = true;
    button.textContent = T.appealing;
    const r = await postAppeal(h.id);
    if (r.status === 201) return onAppealed(r.data.id);
    message.textContent = r.status === 0 ? T.noConnection : r.data.error || T.failed;
    button.textContent = T.appeal;
    button.disabled = r.status === 409;  // already appealed elsewhere: no second try
  });
  return [button, message];
}

export function verdict(root, h, { onNew, onAppealed }) {
  const v = verdictModel(h);
  show(root, el("section", { class: `card verdict outcome-${v.outcome}` },
    v.appeal ? el("p", { class: `appeal-result${h.appeal_accepted ? " accepted" : ""}` }, v.appeal) : null,
    el("div", { class: "judge", "aria-hidden": "true" }, "🪰⚖️"),
    v.topic ? el("p", { class: "topic" }, v.topic) : null,
    el("h2", { class: "headline" }, v.headline),
    v.meters.map(meterNode),
    el("div", { class: "actions" },
      el("button", { class: "primary", onclick: onNew }, T.newArgument),
      v.canAppeal ? appealButton(h, onAppealed) : null,
      v.appealId ? el("button", { class: "secondary", onclick: () => { location.hash = `#/h/${v.appealId}`; } },
        T.toAppeal) : null,
      brainToggle(h))));
  return () => {};
}

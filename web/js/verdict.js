// Verdict screen (SPEC §7, §14.4, P2A-6): the "התיק:" line when there is a topic, the
// outcome headline, an appetite meter per side (A, B MN9 rate), a new-argument button,
// and disabled placeholders for the appeal (P2A-7) and the brain view (P2A-8).
import { el, show } from "./dom.js";
import { T, headline, topicLine } from "./copy.js";

// Pure (tested in Node): what the screen shows for a decided hearing.
export function verdictModel(h) {
  const { A, B } = h.appetite;
  const top = Math.max(A, B), sum = A + B;
  const meter = (s, name, text, rate) => ({
    name, text, winner: h.winner === s,
    share: sum > 0 ? Math.round((100 * rate) / sum) : 0,
    width: top > 0 ? Math.round((100 * rate) / top) : 0,
  });
  return { topic: topicLine(h), headline: headline(h), outcome: h.outcome,
    meters: [meter("A", h.name_a, h.text_a, A), meter("B", h.name_b, h.text_b, B)] };
}

function meterNode(m) {
  return el("div", { class: `meter${m.winner ? " winner" : ""}` },
    el("div", { class: "meter-head" }, el("strong", {}, m.name), el("span", {}, `${T.appetite} ${m.share}%`)),
    el("div", { class: "bar", role: "img", "aria-label": `${T.appetite} ${m.share}%` },
      el("div", { class: "fill", style: `width: ${m.width}%` })),
    el("p", { class: "argument" }, `“${m.text}”`));
}

export function verdict(root, h, onNew) {
  const v = verdictModel(h);
  show(root, el("section", { class: `card verdict outcome-${v.outcome}` },
    el("div", { class: "judge", "aria-hidden": "true" }, "🪰⚖️"),
    v.topic ? el("p", { class: "topic" }, v.topic) : null,
    el("h2", { class: "headline" }, v.headline),
    v.meters.map(meterNode),
    el("div", { class: "actions" },
      el("button", { class: "primary", onclick: onNew }, T.newArgument),
      el("button", { class: "secondary", disabled: true }, T.appealSoon),
      el("button", { class: "secondary", disabled: true }, T.brainSoon))));
  return () => {};
}

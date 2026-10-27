// Verdict screen of a personal page (SPEC §7–§9, §15.4): the appeal's result, the topic,
// the headline (no-show headlines included), an appetite meter per side with both
// arguments, the history, then "send the verdict", the appeal (while allowed) and a new
// case. Live meters and the brain view come in P2B-9.
import { el, show } from "./dom.js";
import { T, topicLine } from "./copy.js";
import { appealLine, clock, historyLine, shareVerdict, verdictHeadline } from "./flow.js";

// Pure (tested in Node): what the screen shows for hearing `n` of a personal view.
export function verdictModel(view, n) {
  const h = view.hearings[n];
  const { A, B } = h.appetite;
  const top = Math.max(A, B), sum = A + B;
  const meter = (s, name, text, rate) => ({
    name, text, winner: h.winner === s,
    share: sum > 0 ? Math.round((100 * rate) / sum) : 0,
    width: top > 0 ? Math.round((100 * rate) / top) : 0,
  });
  return {
    appeal: appealLine(view, h), accepted: Boolean(h.accepted), topic: topicLine(view),
    headline: verdictHeadline(view, h), outcome: h.outcome, history: historyLine(view),
    final: !view.can_appeal && view.hearings.length > 1,
    canAppeal: Boolean(view.can_appeal),
    appealLeft: view.can_appeal ? T.appealLeft(clock(view.appeal_closes_in_s)) : null,
    meters: [meter("A", view.name_a, view.text_a, A),
      meter("B", view.no_show ? T.water : view.name_b, view.no_show ? null : view.text_b, B)],
  };
}

function meterNode(m) {
  return el("div", { class: `meter${m.winner ? " winner" : ""}` },
    el("div", { class: "meter-head" }, el("strong", {}, m.name), el("span", {}, `${T.appetite} ${m.share}%`)),
    el("div", { class: "bar", role: "img", "aria-label": `${T.appetite} ${m.share}%` },
      el("div", { class: "fill", style: `width: ${m.width}%` })),
    m.text ? el("p", { class: "argument" }, `“${m.text}”`) : null);
}

// onAppeal() files the appeal and resolves to an error message, or null when filed.
export function verdictScreen(root, view, n, { onAppeal, publicUrl }) {
  const v = verdictModel(view, n);
  const message = el("p", { class: "error", "aria-live": "polite" });
  const appeal = v.canAppeal ? el("button", { class: "secondary appeal" }, T.appeal) : null;
  if (appeal) {
    appeal.addEventListener("click", async () => {
      appeal.disabled = true;
      appeal.textContent = T.appealing;
      const error = await onAppeal();
      if (!error) return;
      message.textContent = error;
      appeal.textContent = T.appeal;
      appeal.disabled = false;
    });
  }
  show(root, el("section", { class: `card verdict outcome-${v.outcome}` },
    v.appeal ? el("p", { class: `appeal-result${v.accepted ? " accepted" : ""}` }, v.appeal) : null,
    el("div", { class: "judge", "aria-hidden": "true" }, "🪰⚖️"),
    v.topic ? el("p", { class: "topic" }, v.topic) : null,
    el("h2", { class: "headline" }, v.headline),
    v.meters.map(meterNode),
    v.history ? el("p", { class: "history" }, v.history, v.final ? ` · ${T.final}` : "") : null,
    el("div", { class: "actions" },
      el("a", { class: "button wa share", href: shareVerdict(view, view.hearings[n], publicUrl),
        target: "_blank", rel: "noopener" }, T.shareVerdict),
      appeal, v.appealLeft ? el("p", { class: "hint center" }, v.appealLeft) : null, message,
      el("a", { class: "button secondary", href: "/" }, T.newCase)),
    el("p", { class: "note" }, T.personal)));
  return { update: () => {}, stop: () => {} };
}

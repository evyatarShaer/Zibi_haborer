// Verdict screen of a personal page (SPEC §7–§9, §15.4, §15.7): the appeal's result, the
// topic, the headline (no-show headlines included), an appetite meter per side (not on
// Froze) with both arguments, the history, then "send the verdict", the appeal (while
// allowed), the brain view (parties only) and a new case.
import { brainToggle } from "./brain.js";
import { el, show } from "./dom.js";
import { T, topicLine } from "./copy.js";
import { appealLine, clock, shareVerdict } from "./flow.js";
import { flyImg, outcomePose } from "./fly.js";
import { icon, setLabel, withIcon } from "./icons.js";
import { hasMeters, shares } from "./meters.js";

// Pure (tested in Node): what the screen shows for hearing `n` of a personal view.
export function verdictModel(view, n) {
  const h = view.hearings[n];
  const { A, B } = h.appetite;
  const end = shares(A, B, Math.max(A, B));
  const meter = (s, name, text) => ({ name, text, winner: h.winner === s, ...end[s] });
  return {
    appeal: appealLine(view, h), accepted: Boolean(h.accepted), topic: topicLine(view),
    headline: h.headline, outcome: h.outcome, pose: outcomePose(h.outcome), history: view.history,
    final: !view.can_appeal && view.hearings.length > 1,
    canAppeal: Boolean(view.can_appeal), showMeters: hasMeters(h.outcome),
    appealLeft: view.can_appeal ? T.appealLeft(clock(view.appeal_closes_in_s)) : null,
    meters: [meter("A", view.name_a, view.text_a),
      meter("B", view.no_show ? T.water : view.name_b, view.no_show ? null : view.text_b)],
  };
}

// One side: name, appetite bar (when shown) and argument (when there is one).
export function meterNode(m, bar = true) {
  return el("div", { class: `meter${m.winner ? " winner" : ""}` },
    el("div", { class: "meter-head" }, el("strong", {}, m.name, m.winner ? icon("gavel", "icon winner-mark") : null),
      bar ? el("span", { class: "share" }, `${T.appetite} ${m.share}%`) : null),
    bar ? el("div", { class: "bar", role: "img", "aria-label": `${T.appetite} ${m.share}%` },
      el("div", { class: "fill", style: `width: ${m.width}%`, "data-width": m.width })) : null,
    m.text ? el("p", { class: "argument" }, `“${m.text}”`) : null);
}

// The staged reveal: the bars start empty and grow to their width (states.css adds the delay).
function reveal(root) {
  const fills = [...root.querySelectorAll(".verdict .fill")];
  fills.forEach((f) => { f.style.width = "0%"; });
  requestAnimationFrame(() => requestAnimationFrame(() => fills.forEach((f) => {
    f.style.width = `${f.dataset.width}%`;
  })));
}

// onAppeal() files the appeal and resolves to an error message, or null when filed.
// loadBrain() resolves to the API's {status, data} for this hearing's brain summary;
// onShared() reports a "send the verdict" tap (the server counts each case once).
export function verdictScreen(root, view, n, { onAppeal, publicUrl, loadBrain, onShared }) {
  const v = verdictModel(view, n);
  const message = el("p", { class: "error", "aria-live": "polite" });
  const appeal = v.canAppeal ? el("button", { class: "secondary appeal" }, withIcon("again", T.appeal)) : null;
  if (appeal) {
    appeal.addEventListener("click", async () => {
      appeal.disabled = true;
      appeal.classList.add("busy");
      setLabel(appeal, T.appealing);
      const error = await onAppeal();
      if (!error) return;
      message.textContent = error;
      appeal.classList.remove("busy");
      setLabel(appeal, T.appeal);
      appeal.disabled = false;
    });
  }
  show(root, el("section", { class: `card verdict outcome-${v.outcome}` },
    v.appeal ? el("p", { class: `appeal-result${v.accepted ? " accepted" : ""}` }, v.appeal) : null,
    flyImg(v.pose),
    v.topic ? el("p", { class: "topic" }, v.topic) : null,
    el("h2", { class: "headline" }, v.headline),
    v.meters.map((m) => meterNode(m, v.showMeters)),
    v.history ? el("p", { class: "history" }, v.history, v.final ? ` · ${T.final}` : "") : null,
    el("div", { class: "actions" },
      el("a", { class: "button wa share", href: shareVerdict(view, view.hearings[n], publicUrl),
        target: "_blank", rel: "noopener", onclick: onShared }, withIcon("whatsapp", T.shareVerdict)),
      appeal, v.appealLeft ? el("p", { class: "hint center" }, v.appealLeft) : null, message,
      brainToggle({ name_a: view.name_a, name_b: v.meters[1].name }, loadBrain),
      el("a", { class: "button secondary", href: "/" }, withIcon("plus", T.newCase))),
    el("p", { class: "note" }, T.personal)));
  reveal(root);
  return { update: () => {}, stop: () => {} };
}

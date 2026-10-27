// Before the hearing (SPEC §3.1–2, §15.1–2). A's page: the court waits for B, a countdown,
// "send to the other side" and, from 1 h, "nudge again" (both open WhatsApp with B's
// link). B's page: who opened the case and the topic, never A's argument; B writes blind.
import { el, show } from "./dom.js";
import { submitB } from "./api.js";
import { T, topicLine } from "./copy.js";
import { clock, invite, nudge } from "./flow.js";
import { argumentField, feedback, form } from "./input.js";

const abs = (path) => `${location.origin}${path}`;

export function waitAScreen(root, view) {
  const left = el("p", { class: "countdown" });
  const send = el("a", { class: "button wa send", target: "_blank", rel: "noopener" }, T.sendToB);
  const again = el("a", { class: "button secondary nudge", target: "_blank", rel: "noopener" }, T.nudgeB);
  const update = (v) => {
    left.textContent = T.timeLeft(clock(v.deadline_in_s));
    send.href = invite(v, abs(v.link_b));
    again.href = nudge(v, abs(v.link_b));
    again.hidden = !v.nudge;
  };
  show(root, el("section", { class: "card waiting" },
    el("div", { class: "judge buzz", "aria-hidden": "true" }, "🪰"),
    topicLine(view) ? el("p", { class: "topic" }, topicLine(view)) : null,
    el("p", { class: "stage-title" }, T.waitingFor(view.name_b)), left,
    el("div", { class: "actions" }, send, again),
    el("p", { class: "argument" }, `${T.yourArgument}: “${view.text_a}”`),
    el("p", { class: "note" }, T.personal)));
  update(view);
  return { update, stop: () => {} };
}

// onSubmitted(view): B's argument is in; the controller moves on to the story.
export function writeBScreen(root, view, token, onSubmitted) {
  const left = el("p", { class: "countdown" });
  const update = (v) => { left.textContent = T.timeLeft(clock(v.deadline_in_s)); };
  const fields = { text_b: argumentField(T.yourArgument, "text_b") };
  const submit = async (body) => feedback(await submitB(token, body.text_b), onSubmitted);
  show(root, el("section", { class: "card waiting" },
    el("div", { class: "judge", "aria-hidden": "true" }, "🪰"),
    el("p", { class: "stage-title" }, T.summoned(view.name_a)),
    topicLine(view) ? el("p", { class: "topic" }, topicLine(view)) : null, left,
    el("p", { class: "hint center" }, T.blindHintB(view.name_a))),
  form(fields, el("button", { type: "submit", class: "primary" }, T.submitB),
    () => ({ text_b: fields.text_b.input.value }), submit, T.submitting),
  el("p", { class: "note" }, T.personal));
  update(view);
  return { update, stop: () => {} };
}

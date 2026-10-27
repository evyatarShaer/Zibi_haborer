// The public share card, /c/{case id} (SPEC §9): topic, names, the final verdict and its
// history. No arguments and no brain view. Buttons: open a new case, and report, which
// hides the whole case at once (two taps, so it is never hit by accident).
import { el, show } from "./dom.js";
import { getPublic, postReport } from "./api.js";
import { T, topicLine } from "./copy.js";
import { noticeScreen } from "./notice.js";

// Pure (tested in Node).
export function publicModel(c) {
  const decided = c.hearings.filter((h) => h.status === "decided");
  const h = decided[decided.length - 1];
  return {
    topic: topicLine(c), names: `${c.name_a} נגד ${c.name_b}`,
    headline: c.status === "error" ? c.error_message
      : h && c.status !== "hearing" ? h.headline : T.notDecided,
    history: c.history,
  };
}

function reportButton(id, root) {
  const b = el("button", { class: "secondary report" }, T.report);
  b.addEventListener("click", async () => {
    if (!b.classList.contains("sure")) {
      b.classList.add("sure");
      b.textContent = T.reportSure;
      return;
    }
    b.disabled = true;
    const r = await postReport(id);
    if (r.status === 200 || r.status === 404) return noticeScreen(root, T.closed, "closed");
    b.disabled = false;
  });
  return b;
}

export async function publicPage(root, id) {
  const r = await getPublic(id);
  if (r.status !== 200) return noticeScreen(root, r.status === 0 ? T.noConnection : T.closed, "closed");
  publicCard(root, r.data);
}

// The card itself; also what B's link shows after a no-show (nobody is B).
export function publicCard(root, card) {
  const id = card.id, m = publicModel(card);
  show(root, el("section", { class: "card verdict public" },
    el("div", { class: "judge", "aria-hidden": "true" }, "🪰⚖️"),
    m.topic ? el("p", { class: "topic" }, m.topic) : null,
    el("p", { class: "names" }, m.names),
    el("h2", { class: "headline" }, m.headline),
    m.history ? el("p", { class: "history" }, m.history) : null,
    el("div", { class: "actions" }, el("a", { class: "button primary", href: "/" }, T.newCase),
      reportButton(id, root))));
  return { update: () => {}, stop: () => {} };
}

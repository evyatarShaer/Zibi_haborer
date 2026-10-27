// The waiting story (SPEC §14.3, §15.6) for hearing `n` of a personal view: told live
// while it runs, or replayed from stored data when this device has not seen it yet.
// stages.js paces it; update(view) brings each poll in; onDone() once the story ends.
import { el, show } from "./dom.js";
import { T, moodLine } from "./copy.js";
import { step } from "./stages.js";

const TICK_MS = 250;

export function storyScreen(root, view, n, onDone) {
  let v = view;
  const state = {};
  const title = el("p", { class: "stage-title" });
  const line = el("p", { class: "stage-line" });
  show(root, el("section", { class: "card waiting", "aria-live": "polite" },
    el("div", { class: "judge buzz", "aria-hidden": "true" }, "🪰"), title, line,
    el("div", { class: "dots", "aria-hidden": "true" }, el("span"), el("span"), el("span")),
    el("p", { class: "note" }, T.personal)));

  function tick() {
    const h = v.hearings[n];
    const s = step(state, h.status, Date.now());
    if (s.kind === "verdict") {
      clearInterval(ticker);
      return onDone();
    }
    line.textContent = "";
    if (s.kind === "queued") {
      title.textContent = T.queued;
    } else if (s.key === "mood") {
      title.textContent = n > 0 ? T.entersAppeal(h.appealed_by === "A" ? v.name_a : v.name_b) : T.enters;
      line.textContent = moodLine(h.mood, h.wait_h);
    } else if (s.key === "tasteA") {
      title.textContent = T.tasting(v.name_a);
    } else if (s.key === "tasteB") {
      title.textContent = v.no_show ? T.tastingWater : T.tasting(v.name_b);
    } else {
      title.textContent = T.deliberating[s.line % T.deliberating.length];
    }
  }

  const ticker = setInterval(tick, TICK_MS);
  tick();
  return { update: (next) => { v = next; }, stop: () => clearInterval(ticker) };
}

// The waiting story (SPEC §14.3, §15.6) for hearing `n` of a personal view: told live
// while it runs, or replayed from stored data when this device has not seen it yet.
// stages.js paces it; update(view) brings each poll in; onDone() once the story ends.
// The appetite meters fill from the stored MN9 bins (loadBrain): live, in a short reveal
// once the hearing is decided; on a replay (decided when the story starts), during the
// two tasting stages. On Froze there are no meters.
import { el, show } from "./dom.js";
import { T, moodLine } from "./copy.js";
import { hasMeters, replayFill, revealAt } from "./meters.js";
import { step } from "./stages.js";
import { meterNode } from "./verdict.js";

const TICK_MS = 250;

export function storyScreen(root, view, n, onDone, loadBrain) {
  let v = view, brain = null, asked = false, replay;
  const state = {};
  const title = el("p", { class: "stage-title" });
  const line = el("p", { class: "stage-line" });
  const meters = el("div", { class: "live-meters" });
  show(root, el("section", { class: "card waiting", "aria-live": "polite" },
    el("div", { class: "judge buzz", "aria-hidden": "true" }, "🪰"), title, line, meters,
    el("div", { class: "dots", "aria-hidden": "true" }, el("span"), el("span"), el("span")),
    el("p", { class: "note" }, T.personal)));

  async function fetchBrain() {
    asked = true;
    const r = await loadBrain();
    brain = r.status === 200 ? r.data : { failed: true };
  }

  // The two meters, built once and then filled in place (the bars' CSS eases each step).
  function fill(pA, pB) {
    const now = revealAt(brain, pA, pB);
    if (!meters.children.length) {
      meters.replaceChildren(meterNode({ name: v.name_a, share: 0, width: 0 }),
        meterNode({ name: v.no_show ? T.water : v.name_b, share: 0, width: 0 }));
    }
    ["A", "B"].forEach((s, i) => {
      const m = meters.children[i];
      m.querySelector(".fill").style.width = `${now[s].width}%`;
      m.querySelector(".share").textContent = `${T.appetite} ${now[s].share}%`;
    });
  }

  function tick() {
    const h = v.hearings[n];
    const decided = h.status === "decided", wanted = decided && hasMeters(h.outcome);
    if (replay === undefined) replay = decided;
    if (wanted && !asked) fetchBrain();
    const ready = wanted && brain !== null && !brain.failed;
    // Live, decided but its curves still on the way: keep deliberating a moment.
    const status = wanted && brain === null && !replay ? "running" : h.status;
    const s = step(state, status, Date.now(), ready && !replay);
    if (s.kind === "verdict") {
      clearInterval(ticker);
      return onDone();
    }
    if (s.kind === "reveal") {
      title.textContent = T.revealing;
      line.textContent = "";
      return fill(s.p, s.p);
    }
    const at = replay && ready && s.kind === "stage" ? replayFill(s.key, s.p) : null;
    if (at) fill(...at);
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

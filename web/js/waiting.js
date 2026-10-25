// Waiting screen (SPEC §14.3, P2A-5): polls GET /hearing/{id} and tells the story from
// stages.js. Something always moves (the buzzing fly, the dots). Queued → a "waiting in
// line" line first; failed → a Hebrew error with a retry; unknown id → not found.
import { el, show } from "./dom.js";
import { getHearing } from "./api.js";
import { T, moodLine } from "./copy.js";
import { step } from "./stages.js";
import { submit } from "./input.js";
import { load, save } from "./session.js";

const POLL_MS = 700;
const TICK_MS = 250;
const OFFLINE_AFTER = 5;

export function waiting(root, id, fresh, { onVerdict, onNew, onSubmitted }) {
  let h = null, misses = 0, stopped = false;
  const state = {};
  const title = el("p", { class: "stage-title" });
  const line = el("p", { class: "stage-line" });
  const note = el("p", { class: "hint" });
  show(root, el("section", { class: "card waiting", "aria-live": "polite" },
    el("div", { class: "judge buzz", "aria-hidden": "true" }, "🪰"), title, line,
    el("div", { class: "dots", "aria-hidden": "true" }, el("span"), el("span"), el("span")), note));

  const stop = () => { stopped = true; clearInterval(poller); clearInterval(ticker); };
  const ending = (text, ...buttons) => {
    stop();
    show(root, el("section", { class: "card waiting" }, el("div", { class: "judge" }, "🪰"),
      el("p", { class: "stage-title" }, text), ...buttons,
      el("button", { class: "secondary", onclick: onNew }, T.newArgument)));
  };
  const retry = async () => {
    const body = load("lastBody");
    const out = body ? await submit(body) : {};
    if (out.id) return onSubmitted(out.id);
    save("draft", body);
    onNew();
  };

  async function poll() {
    const r = await getHearing(id);
    if (stopped) return;
    if (r.status === 404) return ending(T.notFound);
    if (r.status !== 200) {
      misses += 1;
      note.textContent = misses >= OFFLINE_AFTER ? T.noConnection : "";
      return;
    }
    misses = 0;
    note.textContent = "";
    if (h === null && !fresh && r.data.status === "decided") {
      stop();
      return onVerdict(r.data);  // reopened link: no story
    }
    h = r.data;
  }

  function tick() {
    if (h === null) return;
    const v = step(state, h.status, Date.now());
    if (v.kind === "failed") return ending(T.failed, el("button", { class: "primary", onclick: retry }, T.retry));
    if (v.kind === "verdict") {
      stop();
      return onVerdict(h);
    }
    if (v.kind === "queued") {
      title.textContent = T.queued;
      line.textContent = "";
    } else if (v.key === "mood") {
      title.textContent = h.appeal_of ? T.entersAppeal : T.enters;
      line.textContent = moodLine(h.mood);
    } else if (v.key === "tasteA" || v.key === "tasteB") {
      title.textContent = T.tasting(v.key === "tasteA" ? h.name_a : h.name_b);
      line.textContent = "";
    } else {
      title.textContent = T.deliberating[v.line % T.deliberating.length];
      line.textContent = "";
    }
  }

  const poller = setInterval(poll, POLL_MS);
  const ticker = setInterval(tick, TICK_MS);
  poll();
  return stop;
}

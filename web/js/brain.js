// "What happened in the brain?" (SPEC §14.6, P2A-8): a toggle under the verdict. The
// summary is fetched once, on the first open; the drawing comes from lab.js.
import { el, svg } from "./dom.js";
import { getBrain } from "./api.js";
import { LAB, T } from "./copy.js";
import { CHART, labModel } from "./lab.js";

const SIDES = ["a", "b"];

function mn9Chart(m, names) {
  const c = m.chart;
  const readout = el("p", { class: "readout", "aria-live": "polite" }, " ");
  const cursor = svg("line", { class: "cursor", y1: CHART.top, y2: CHART.h - CHART.bottom, visibility: "hidden" });
  const point = (e) => {
    const box = e.currentTarget.getBoundingClientRect();
    const i = c.nearest(((e.clientX - box.left) / box.width) * CHART.w);
    cursor.setAttribute("x1", c.xs[i]);
    cursor.setAttribute("x2", c.xs[i]);
    cursor.setAttribute("visibility", "visible");
    readout.textContent = LAB.at(c.times[i], names.map((n, s) => `${n} ${LAB.hz(m.curves[s][i])}`));
  };
  const plot = svg("svg", { viewBox: `0 0 ${CHART.w} ${CHART.h}`, class: "chart", direction: "ltr",
    role: "img", "aria-label": LAB.mn9, onpointerdown: point, onpointermove: point },
  c.yTicks.map((t) => [
    svg("line", { class: "grid", x1: CHART.left, x2: CHART.w - CHART.right, y1: t.y, y2: t.y }),
    svg("text", { class: "tick", x: CHART.left - 4, y: t.y + 4, "text-anchor": "end" }, String(t.hz)),
  ]),
  c.xTicks.map((t) => svg("text", { class: "tick", x: t.x, y: CHART.h - 6, "text-anchor": "middle" },
    `${t.s} ${LAB.seconds}`)),
  cursor,
  c.lines.map((pts, s) => svg("polyline", { class: `curve lab-${SIDES[s]}`, points: pts })));
  return [legend(names), plot, readout];
}

const legend = (names) => el("div", { class: "legend" },
  names.map((n, s) => el("span", {}, el("i", { class: `swatch lab-${SIDES[s]}` }), n)));

function tasteBars(m, names) {
  return el("div", { class: "taste" }, legend(names), m.taste.map((r) => el("div", { class: "taste-row" },
    el("span", { class: "taste-label" }, r.label),
    SIDES.map((k, s) => el("div", { class: "taste-bar", title: `${names[s]} ${LAB.hz(r.hz[s])}` },
      el("div", { class: `fill lab-${k}`, style: `width: ${r.width[s]}%` }),
      el("span", {}, LAB.hz(r.hz[s])))))));
}

function facts(m) {
  const row = (k, v) => [el("dt", {}, k), el("dd", {}, v)];
  return el("dl", { class: "facts" }, row(LAB.hunger, m.mood.hunger), row(LAB.irritability, m.mood.arousal),
    row(LAB.seed, m.seed), row(LAB.version, m.simVersion), row(LAB.platform, m.platform));
}

export function labView(b, h) {
  const m = labModel(b), names = [h.name_a, h.name_b];
  return el("section", { class: "card lab" },
    el("h3", {}, LAB.title), el("p", { class: "no-ai" }, LAB.noAi),
    el("h4", {}, LAB.mn9), el("p", { class: "hint" }, LAB.mn9Hint), mn9Chart(m, names),
    el("h4", {}, LAB.taste), el("p", { class: "hint" }, LAB.tasteHint), tasteBars(m, names),
    el("h4", {}, LAB.judge), facts(m));
}

// The toggle button and the place the lab view opens into.
export function brainToggle(h) {
  const slot = el("div");
  let open = false, loaded = null;
  const button = el("button", { class: "secondary", "aria-expanded": "false" }, T.brain);
  const set = (isOpen) => {
    open = isOpen;
    button.textContent = open ? T.brainHide : T.brain;
    button.setAttribute("aria-expanded", String(open));
    slot.replaceChildren(...(open && loaded ? [loaded] : []));
  };
  button.addEventListener("click", async () => {
    if (open || loaded) return set(!open);
    button.disabled = true;
    button.textContent = T.brainLoading;
    const r = await getBrain(h.id);
    button.disabled = false;
    if (r.status !== 200) {
      button.textContent = T.brain;
      slot.replaceChildren(el("p", { class: "error" }, r.data.error || LAB.error));
      return;
    }
    loaded = labView(r.data, h);
    set(true);
    loaded.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  return [button, slot];
}

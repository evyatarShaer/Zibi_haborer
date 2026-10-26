// The lab view's numbers (SPEC §14.6, P2A-8), pure so Node can test them: the two MN9
// curves as SVG polylines, the judge's mood and the run's identity (no taste classes,
// SPEC §15.7).
// Everything comes from the stored brain summary; nothing here asks the simulation.
export const CHART = { w: 320, h: 170, left: 34, right: 8, top: 10, bottom: 24 };
const SMOOTH = 5; // bins in the display-only moving average (5 × 50 ms)

// Centered moving average; the ends average what they have.
export function smooth(xs, k = SMOOTH) {
  const half = Math.floor(k / 2);
  return xs.map((_, i) => {
    const win = xs.slice(Math.max(0, i - half), i + half + 1);
    return win.reduce((a, b) => a + b, 0) / win.length;
  });
}

// Round up to a readable axis top: a multiple of 10 (≤ 100) or of 50.
export function niceTop(x) {
  const step = x <= 100 ? 10 : 50;
  return Math.max(step, Math.ceil(x / step) * step);
}

function chart(curves, binS) {
  const { w, h, left, right, top, bottom } = CHART;
  const n = curves[0].length, dur = n * binS;
  const yTop = niceTop(Math.max(...curves.flat()));
  const x = (s) => left + ((w - left - right) * s) / dur;
  const y = (hz) => top + (h - top - bottom) * (1 - hz / yTop);
  const times = curves[0].map((_, i) => (i + 0.5) * binS);
  const xTicks = [];
  for (let s = 0; s <= dur + 1e-9; s += 0.5) xTicks.push({ s, x: x(s) });
  return {
    yTop, dur, times,
    lines: curves.map((c) => c.map((hz, i) => `${x(times[i]).toFixed(1)},${y(hz).toFixed(1)}`).join(" ")),
    yTicks: [0, yTop / 2, yTop].map((hz) => ({ hz, y: y(hz) })),
    xTicks,
    xs: times.map(x),
    // index of the bin nearest to an x in chart units (for the tap readout)
    nearest: (px) => Math.min(n - 1, Math.max(0, Math.round(((px - left) / (w - left - right)) * dur / binS - 0.5))),
  };
}

export function labModel(b) {
  const curves = b.mn9_hz.map((c) => smooth(c));
  return {
    curves,
    chart: chart(curves, b.bin_ms / 1000),
    mood: { hunger: b.mood.hunger.toFixed(2), arousal: b.mood.arousal.toFixed(2) },
    seed: String(b.seed), simVersion: b.sim_version, platform: b.platform,
  };
}

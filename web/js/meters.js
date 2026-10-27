// Appetite meters (SPEC §7, §15.6), pure so Node can test them. During the story they fill
// from the stored MN9 bins: each side shows the cumulative rate of its tasting so far,
// and at the end the stored A/B rates exactly (rate = mean of the bins over the tasting).
// Hidden on Froze.
export const hasMeters = (outcome) => outcome !== "froze";

// Mean of the first ⌈p·n⌉ bins: the tasting's rate so far (0 before the first bin).
export function cumulative(bins, p) {
  const k = Math.min(bins.length, Math.ceil(p * bins.length));
  return k > 0 ? bins.slice(0, k).reduce((a, b) => a + b, 0) / k : 0;
}

// Each side's share of the summed rate (%) and bar width against `top` (%).
export function shares(a, b, top) {
  const sum = a + b;
  const one = (x) => ({ share: sum > 0 ? Math.round((100 * x) / sum) : 0,
    width: top > 0 ? Math.round((100 * Math.min(x, top)) / top) : 0 });
  return { A: one(a), B: one(b) };
}

// The meters `p` (0–1) of the way through the reveal; bars are scaled to the final top.
export function revealAt(brain, p) {
  const [a, b] = brain.mn9_hz;
  const top = Math.max(cumulative(a, 1), cumulative(b, 1));
  return shares(cumulative(a, p), cumulative(b, p), top);
}

// Waiting screen story (SPEC §14.3). The two tastings run at once; the order is told.
// Each stage shows for at least its minimum, so a fast verdict still reads as a story;
// "deliberate" then cycles its lines until the verdict is in. Pure: tested in Node.
export const STAGES = [["mood", 2200], ["tasteA", 1800], ["tasteB", 1800], ["deliberate", 1200]];
export const STORY_MS = STAGES.reduce((sum, [, ms]) => sum + ms, 0);
export const CYCLE_MS = 2000;
export const REVEAL_MS = 2000; // live: the appetite meters fill after the story (SPEC §15.6)

// The stage `t` ms into the story: `p` is how far into it (0–1; 1 for deliberate, which
// has no end), `line` counts deliberate's cycles from 0.
export function stageAt(t) {
  let start = 0;
  for (const [key, ms] of STAGES.slice(0, -1)) {
    if (t < start + ms) return { key, line: 0, p: (t - start) / ms };
    start += ms;
  }
  return { key: "deliberate", line: Math.floor((t - start) / CYCLE_MS), p: 1 };
}

// What the screen shows now. `state` ({} at first) remembers when the story started
// (when the hearing left the queue) and when the reveal started. The verdict waits for
// the story to finish; with `reveal`, the meters fill for REVEAL_MS first.
export function step(state, status, now, reveal = true) {
  if (state.start === undefined) {
    if (status === "queued") return { kind: "queued" };
    state.start = now;
  }
  const t = now - state.start;
  if (status !== "decided" || t < STORY_MS) return { kind: "stage", ...stageAt(t) };
  if (!reveal) return { kind: "verdict" };
  if (state.reveal === undefined) state.reveal = now;
  const r = now - state.reveal;
  return r >= REVEAL_MS ? { kind: "verdict" } : { kind: "reveal", p: r / REVEAL_MS };
}

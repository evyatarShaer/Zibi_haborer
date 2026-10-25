// Waiting screen story (SPEC §14.3). The two tastings run at once; the order is told.
// Each stage shows for at least its minimum, so a fast verdict still reads as a story;
// "deliberate" then cycles its lines until the verdict is in. Pure: tested in Node.
export const STAGES = [["mood", 2200], ["tasteA", 1800], ["tasteB", 1800], ["deliberate", 1200]];
export const STORY_MS = STAGES.reduce((sum, [, ms]) => sum + ms, 0);
export const CYCLE_MS = 2000;

// The stage `t` ms into the story; `line` counts deliberate's cycles from 0.
export function stageAt(t) {
  let end = 0;
  for (const [key, ms] of STAGES.slice(0, -1)) {
    end += ms;
    if (t < end) return { key, line: 0 };
  }
  return { key: "deliberate", line: Math.floor((t - end) / CYCLE_MS) };
}

// What the screen shows now. `state` ({} at first) remembers when the story started:
// when the hearing left the queue. The verdict waits for the story to finish.
export function step(state, status, now) {
  if (status === "failed") return { kind: "failed" };
  if (state.start === undefined) {
    if (status === "queued") return { kind: "queued" };
    state.start = now;
  }
  const t = now - state.start;
  if (status === "decided" && t >= STORY_MS) return { kind: "verdict" };
  return { kind: "stage", ...stageAt(t) };
}

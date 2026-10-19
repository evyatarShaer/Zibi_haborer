---
name: phase-gate
description: Use before declaring a phase done or starting the next one. Reads the phase's exit criteria from docs/SPEC.md, demands concrete evidence for each, and only then updates docs/TASKS.md and tags the commit. Prevents moving on with unmet criteria.
---

# phase-gate

A gate, not a checkbox. Don't declare a phase done without running
this.

## Steps

1. **Read exit criteria.** Open `docs/SPEC.md §12` and list the exit
   criteria for the phase in question.
2. **Collect evidence.** For each criterion, show concrete evidence:
   - test name + a line or two of real output
   - measured numbers (not estimates)
   - links to notebooks, reports, or `docs/POC_REPORT.md`
3. **If any criterion fails:** list exactly what's missing and stop.
   Do not update tasks, do not tag, do not open a Phase N+1 Epic.
4. **If all criteria pass:**
   - Update `docs/TASKS.md`: check off all Phase N tasks; open the
     Phase N+1 Epic skeleton.
   - Tag the current commit: `phase-1-done`, `phase-2-done`, etc.
   - Write a one-paragraph summary in `docs/DECISIONS.md` under a dated
     heading `## YYYY-MM-DD — Phase N gate passed`.
5. **Report back** with the evidence table and the tag name.

## Rules

- **Don't lower a criterion to pass the gate.** If a target is wrong,
  change it in `SPEC.md` *before* re-running the gate, and record why
  in `DECISIONS.md`.
- **No "mostly done" phases.** A phase either passes every exit
  criterion or it doesn't pass.
- **Numbers, not vibes.** "Runs fast" is not evidence. "p95 wall-clock
  = 11.2 s across 1,000 runs" is.

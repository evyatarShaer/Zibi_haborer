---
name: sim-change
description: Use before, during, and after any change to sim/src/borer_sim/ — the model, letter→glomerulus mapping, mood, readout, or thresholds. Enforces version bump, determinism check, balance check, and a DECISIONS.md entry so verdicts stay reproducible across versions.
---

# sim-change

Any change to `sim/src/borer_sim/` runs through this skill. The
simulator is the product; silent changes break determinism guarantees.

## Required steps for every change

1. **Bump `SIM_VERSION`** in `sim/src/borer_sim/version.py` (semver:
   patch for internal refactors with identical output, minor for
   behavior changes, major for breaking changes). The number is logged
   with every `Run` row.
2. **Determinism test.**
   `pytest sim/tests/test_determinism.py` — same input twice → identical
   metrics (bit-for-bit on `margin`, `decision_time_ms`,
   `direction_flips`, `active_neurons`, `deciding_neuron`,
   `giant_fiber_fired`).
3. **Balance test.**
   `pytest sim/tests/test_balance.py` — 1,000 seeded random argument
   pairs. Side A win rate **and** left-antenna win rate must each land
   in **45–55%**. Swap test (200 pairs, X/Y then Y/X, same seed): winner
   flips in **≥ 75%** of decided cases. Outcome mix: Win ≥ 50%, each
   special outcome ≤ 15%. Report:
   - margin distribution (histogram, percentiles)
   - outcome frequencies (Win / Tie / Fled / Froze / Dithered /
     Went-for-food)
4. **Performance measurement.**
   - Record median and p95 wall-clock per run (target ≤ 15 s).
   - Record peak RSS (target ≪ 12 GB).
5. **Log the change in `docs/DECISIONS.md`** with:
   - what changed and why
   - all numbers from steps 3–4
   - the new `SIM_VERSION`

## Guardrails

- **No new sources of randomness without an explicit seed path.** Every
  stochastic step takes a seed derived from `case.seed`.
- **No AI/LLM in `borer_sim/`.** Ever.
- **If a change breaks the balance test**, don't tune thresholds to
  mask it. Investigate the mechanism (mapping imbalance, saturation,
  mood coupling) and fix the mechanism.
- **Document surprise.** If a change produces an unexpected outcome
  shift, record it in `DECISIONS.md` even if the numbers still pass —
  future-us will want to know.

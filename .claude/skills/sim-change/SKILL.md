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
   `pytest sim/tests/test_determinism.py sim/tests/test_hearing.py`.
   Same input twice must give identical spikes and an identical product
   hearing (metrics, outcome, brain summary), bit for bit.
3. **Balance test** (SPEC §12 exit criteria).
   `pytest sim/tests/test_balance.py` checks the stored balance run
   (`validation.balance`: 1,000 seeded random argument pairs, product
   mood).
   - **Patch** (identical output): rerun `validation.balance time`. All
     20 hearings must match the stored records (`records_match` 20/20).
   - **Minor/major** (output changes): rerun `validation.balance run`
     (detached, ~3–5 h), then `time`.

   Criteria:
   - side A wins **45–55%** of decided hearings;
   - seed consistency: **≥ 90%** of non-trivial pairs (mean gap ≥ 10%)
     keep their winner in **≥ 75%** of seeds;
   - outcome mix: Win **≥ 50%**, each special outcome (Froze / Lunch
     break / Dithered) **≤ 15%**;
   - MN9 range continuous (**≤ 50%** of tastings in any 10%-of-range
     band);
   - |Spearman ρ| **< 0.5** of per-argument MN9 with length and with
     the ד/ב/ש count;
   - longer argument wins **40–60%**;
   - runaway (> 4,000 active) **< 2%** of tastings.

   Report:
   - gap distribution (percentiles);
   - outcome frequencies (Win / Tie / Froze / Dithered / Lunch break).
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

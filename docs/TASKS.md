# Tasks

> Lightweight replacement for Jira (no Jira MCP available in this
> environment). One Epic per phase. Check off tasks as they complete.

## Epic: Phase 1 — POC

**Goal:** prove that a connectome-driven simulation can produce
deterministic, roughly-balanced verdicts from text inputs within the
performance budget.

**Exit criteria** (from `SPEC.md §12`):
- balance: 1,000 random pairs → side A wins 45–55%
- seed consistency: ≥ 90% of non-trivial pairs (mean gap ≥ 10%) keep
  their winner in ≥ 75% of seeds
- outcome mix: Win ≥ 50%; each special outcome ≤ 15%
- input quality: MN9 range continuous; |ρ| < 0.5 with length and ד/ב/ש
  count; longer argument wins 40–60% (all pairs of the set); runaway
  < 2% of tastings
- hearing ≤ 15 s (two 1.5 s tastings)
- RAM fits in 12 GB (ideally much less)

### Tasks

- [x] **P1-1 — Environment.** WSL2 + Python 3.12 + `uv`. Project in
  `sim/` with `pyproject.toml`. Deps: `torch`, `numpy`, `pandas`,
  `pyarrow`, `pytest`, `jupyter` (`brian2` only for validation).
- [x] **P1-2 — Locate data.** Find official FlyWire v783 downloads
  (FlyWire Codex) and Shiu et al. 2024's published code (likely GitHub
  `philshiu/Drosophila_brain_model` — **verify**). If downloads need a
  login, stop and tell the user which files to download and where.
  *Done 2026-10-19: 3 files downloaded + verified (sha256, schemas) —
  see `docs/DATA_SOURCES.md`.*
- [x] **P1-3 — Validate baseline.** Reproduce one known result from
  Shiu's model (e.g. sugar-sensing neurons activating feeding-related
  neurons).
  *Done 2026-10-20: sugar GRNs → MN9 reproduced on v783, 7/7 checks —
  see `docs/POC_REPORT.md`.*
- [x] **P1-4 — Fill flywire-data skill.** Replace placeholders with real
  column names, IDs, side labels, and the specific IDs for V (CO₂), DA2
  (geosmin), DNa02 family, Giant Fiber (DNp01 — verify).
  *Done 2026-10-20: skill verified, `borer_sim.anatomy` added, side =
  fly's own side — see DECISIONS.md.*
- [x] **P1-5 — Implement LIF in PyTorch.** Match Shiu's outputs on the
  same input within tolerance.
  *Done 2026-10-20: 13/13 checks vs Brian2; 2 s run 13.05 s at 2
  threads — see `docs/POC_REPORT.md`.*
- [x] **P1-6 — Implement taste.py.** Normalization, letter→GRN group
  table (v4), saturation, `!`/`?` handling, side balancing. Unit tests.
  *Done 2026-10-22 (SIM_VERSION 0.6.0). Ported 2026-10-22 ("taste of
  words" replaced "smell of words", SPEC §4; 0.5.0), then reopened the
  same day: spamming one letter defeated saturation. Fixed with a
  per-group cap (120 Hz), coverage scaling, no-Hebrew baseline and
  r_base 2 Hz: the spam/silence suite passes (no runaway, strongest spam
  דבש × 93 at 21.5 Hz < natural P75) and OLD+NEW + THIRD pass every
  criterion, with longer-wins now measured over all pairs (changed after
  seeing THIRD's 39% on 30 probe pairs; 47% on all 190) — see
  DECISIONS.md 2026-10-22.*
- [x] **P1-7 — Implement mood.py.** Hunger and arousal with their
  effects.
  *Done 2026-10-24 (SIM_VERSION 0.7.0). Hunger gain 0.5 on class-E
  groups; arousal = random-sign 2 mV noise kicks up to 10 Hz (20 Hz
  ignites runaways). On OLD+NEW mood changes 10.5% of verdicts, flips
  3.2% of winners; runaway 0.9% of tastings — DECISIONS.md 2026-10-24.*
- [x] **P1-8 — Implement readout.py.** A hearing = two tastings (one
  per argument, same seed, 1.5 s each, run in parallel). Readout = MN9
  (L + R) per tasting → `A`, `B`, `margin`, `gap`; `decision_time_ms`
  and `direction_flips` from the binned A − B; `active_neurons`;
  `deciding_neuron` (more active MN9 of the winning tasting);
  Outcomes per SPEC §7: Froze (both MN9 < 6 Hz) → Went for food
  (hunger > 0.8, gap < 5%) → Dithered (≥ 8 flips, gap < 5%) → Win
  (gap ≥ 5%) → Plain tie.
  *Done 2026-10-24 (SIM_VERSION 0.7.0). Thresholds calibrated on 600
  OLD+NEW hearings by a rule fixed before running: froze 2 → 6 Hz, flips
  3 → 8; mix Win 96.2%, dithered 3.2%, tie 0.3%, froze 0.2%, food 0.2%.
  Fled dropped: GF fired in 0/1,200 tastings — DECISIONS.md 2026-10-24.*
- [x] **P1-9 — Determinism + balance tests.** Determinism: same input
  twice → identical metrics. `test_balance.py`: balance (1,000 seeded
  random pairs, side A wins 45–55%), seed consistency (≥ 90% of
  non-trivial pairs keep their winner in ≥ 75% of seeds) and outcome
  mix (Win ≥ 50%, each special outcome ≤ 15%), exactly as in the exit
  criteria above. Measure hearing time and peak RAM. Platform recorded
  once per run in DECISIONS.md (amended 2026-10-25; result rows carry
  a `platform` field from then on, no backfill).
  *Done 2026-10-25 (SIM_VERSION 0.8.0), `tests/test_balance.py` 8/8: side
  A 46.3% (415/897); seed consistency 32/35 = 91.4%; mix win 89.7%,
  dithered 8.2%, food 1.7%, tie 0.4%, froze 0; runaway 0.38%; longer
  wins 44.7%; hearing median 6.69 s, 20/20 match the records; peak RSS
  1.98 GB + 1.14 GB per child. Platform in DECISIONS.md 2026-10-25.*
- [x] **P1-10 — Subcircuit (if needed).** Only if full-brain runs blow
  the budget. Compare against full-brain results.
  *Not needed 2026-10-25: N = 6 matched the full brain but gave no
  speed-up, and full-brain hearings take 6.7 s (budget 15 s).
  `borer_sim.subcircuit` is kept but not adopted.*
- [x] **P1-11 — docs/POC_REPORT.md.** All numbers + decisions made during
  POC. *Done 2026-10-25: P1-9, P1-10, timing scope and summary sections;
  input quality re-measured at 0.8.0 on the balance data (band 24.3%,
  ρ length −0.07, ρ ד/ב/ש +0.01).*
- [x] **P1-12 — Run `phase-gate` skill.** Confirm every exit criterion.
  *Passed 2026-10-25, tag `phase-1-done` (DECISIONS.md 2026-10-25 —
  Phase 1 gate passed).*

## Epic: Phase 2 — MVP

**Goal** (SPEC §12): full flow, verdict card, OG preview, animation, all
tie types, sudden death, how-it-works page.

**Exit criteria** (from `SPEC.md §12`):
- 20 real cases in friends' groups, ≥ half shared onward.

**Carried over from Phase 1** (POC_REPORT.md summary): production-host
timing (deployment); "Brain overload" outcome decision; rename "Went for
food"; real-utterance arguments; watch side-A (46.3%) and shorter-wins
(44.7%) drift; FlyWire licence (non-commercial).

### Tasks

Not yet planned (next session: break the MVP scope into P2-n tasks).

## Epic: Phase 3

Not yet planned.

# Tasks

> Lightweight replacement for Jira (no Jira MCP available in this
> environment). One Epic per phase. Check off tasks as they complete.

## Epic: Phase 1 — POC

**Goal:** prove that a connectome-driven simulation can produce
deterministic, roughly-balanced verdicts from text inputs within the
performance budget.

**Exit criteria** (from `SPEC.md §12`):
- balance: 1,000 random pairs → side A wins 45–55% and left antenna
  wins 45–55%
- swap test: 200 pairs, (X,Y) vs (Y,X) → winner flips in ≥ 75% of
  decided cases
- outcome mix: Win ≥ 50%; each special outcome ≤ 15%
- run ≤ 15 s per hearing
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
- [ ] **P1-3 — Validate baseline.** Reproduce one known result from
  Shiu's model (e.g. sugar-sensing neurons activating feeding-related
  neurons).
- [ ] **P1-4 — Fill flywire-data skill.** Replace placeholders with real
  column names, IDs, side labels, and the specific IDs for V (CO₂), DA2
  (geosmin), DNa02 family, Giant Fiber (DNp01 — verify).
- [ ] **P1-5 — Implement LIF in PyTorch.** Match Shiu's outputs on the
  same input within tolerance.
- [ ] **P1-6 — Implement smell.py.** Normalization, letter→glomerulus
  mapping, saturation, `!`/`?` handling. Unit tests.
- [ ] **P1-7 — Implement mood.py.** Hunger and arousal with their
  effects.
- [ ] **P1-8 — Implement readout.py.** All metrics and outcome
  classification.
- [ ] **P1-9 — Determinism + balance tests.** Determinism: same input
  twice → identical metrics. Balance, swap test and outcome mix
  exactly as in the exit criteria above. Measure runtime and peak RAM.
  Record `platform` with every run.
- [ ] **P1-10 — Subcircuit (if needed).** Only if full-brain runs blow
  the budget. Compare against full-brain results.
- [ ] **P1-11 — docs/POC_REPORT.md.** All numbers + decisions made during
  POC.
- [ ] **P1-12 — Run `phase-gate` skill.** Confirm every exit criterion.

## Epic: Phase 2 — MVP

Not yet planned. Will be filled after Phase 1 passes the gate.

## Epic: Phase 3

Not yet planned.

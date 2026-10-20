# POC report (Phase 1)

Numbers and decisions from the POC, per task. Filled in as tasks finish.

## P1-3 — Baseline validation (Shiu et al. 2024)

**Result: PASS (7/7 checks).** Run 2026-10-19 → 2026-10-20.

### What was reproduced

Shiu et al. 2024, Fig. 1 / Fig. 3A: activating labellar **sugar** GRNs
drives **MN9** (proboscis-extension motor neuron); co-activating
**bitter** GRNs suppresses it.

- **Model:** `sim/validation/shiu_brian2.py` — a Brian2 port of Shiu's
  `model.py` (same LIF equations, parameters, Poisson drive at
  `w_syn × f_poi`), whole brain: 138,639 neurons, 15,091,983 edges,
  FlyWire **v783** via `borer_sim.data`.
- **Inputs:** Shiu's v630 sugar/bitter GRN lists (`figures.ipynb`),
  keeping the IDs unchanged in v783: **20 / 21 sugar** and **20 / 21
  bitter**. Each driven at **200 Hz**.
- **Readout:** MN9 pair = `720575940660219265` (Shiu's `id_mn9`) and
  its `CB0701` partner `720575940618238523`.
- **Trials:** 30 × 1 s per condition, seed 783 (trial k → seed 783 + k).
- **Reference:** Shiu's published output `results/example/sugarR.parquet`
  (v630, 21 sugar GRNs at 200 Hz, 30 trials) — see `DATA_SOURCES.md`.
- **Script:** `PYTHONPATH=src uv run python -m validation.sugar_mn9 30`
  (from `sim/`); full output in `sim/data/processed/validation/`.

Pass criteria were fixed before the run: ±30% of the v630 reference
where one exists (it covers the sugar condition only), qualitative
agreement with the paper otherwise.

### Results (mean over 30 trials)

| Condition | MN9 (Shiu id) Hz | MN9 partner Hz | Active neurons | Spikes / trial |
|---|---|---|---|---|
| Baseline (no input) | 0.0 | 0.0 | 0 | 0 |
| Sugar 200 Hz | **89.9** | **62.8** | **395** | 16,120 |
| Bitter 200 Hz | 0.0 | 0.0 | 83 | 6,052 |
| Sugar + bitter 200 Hz | 6.8 | 11.7 | 352 | 16,528 |
| *Reference: Shiu v630, sugar 200 Hz* | *93.3* | *61.8* | *448* | — |

### Checks

| Check | Criterion | Value | Result |
|---|---|---|---|
| Determinism | same seed → identical spike counts (2 trials, fresh build) | identical | PASS |
| Baseline | no spikes without input | 0 spikes | PASS |
| Sugar → MN9 (Shiu id) | within ±30% of 93.3 Hz | 89.9 Hz (−3.6%) | PASS |
| Sugar → MN9 partner | within ±30% of 61.8 Hz | 62.8 Hz (+1.7%) | PASS |
| Sugar → active neurons | within ±30% of 448 | 395 (−11.8%) | PASS |
| Bitter alone | MN9 silent (no published number) | 0.0 / 0.0 Hz | PASS |
| Bitter suppresses sugar | MN9 lower than sugar alone (Fig. 3A, qualitative) | 89.9 → 6.8 Hz | PASS |

### Notes

- **Side labels are mirrored** between Shiu 2024 and the v783
  annotations (his "right" sugar GRNs are `side == "left"`). Logged in
  `DECISIONS.md`; matters for the turning readout in P1-8.
- One of the 21 sugar GRNs and one of the 21 bitter GRNs changed
  root_id between v630 and v783 and were dropped; this plus v783
  rewiring is the likely cause of the lower active-neuron count.
- **Performance (Brian2, Cython, 1 core):** about 6 s per 1 s trial
  (sugar: 30 trials in 181 s including the build); peak RSS about
  2.2 GB. The total run took 32 min of CPU. Wall-clock per condition in
  the JSON is inflated by the PC sleeping overnight and is not a
  measurement. This is the baseline P1-5's PyTorch model must match on
  output and beat on speed (target ≤ 15 s per hearing).

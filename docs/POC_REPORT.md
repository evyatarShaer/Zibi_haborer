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

## P1-5 — PyTorch LIF model vs Brian2

**Result: PASS (13/13 checks).** Run 2026-10-20. `SIM_VERSION` 0.1.0.

- **Model:** `sim/src/borer_sim/model.py` — CPU PyTorch, float32, exact
  linear integration at 0.1 ms, CSR delivery of only the neurons that
  spiked, Brian2's step order. Constants from `borer_sim/params.py`
  (shared with the Brian2 port).
- **Found while matching:** Brian2's `(unless refractory)` is a
  *conditional write*. Synaptic input that reaches a refractory neuron
  is **discarded**, not deferred. The first torch version let `g`
  accumulate during refractoriness and ran about 25% hot (MN9
  114–125 Hz). Matching the conditional write fixed it. Shiu's
  published numbers include this behaviour, so it is part of "the
  model".
- **Exact-equivalence test:** `tests/test_model_vs_brian2.py` drives a
  3-neuron net (with inhibition) at p = 1, so both engines get identical
  input. Spike trains are identical over 500 ms.
- **Statistical comparison:** `validation/torch_vs_brian2.py`, the four
  P1-3 conditions, 30 × 1 s trials, seeds 783 + k, 2 torch threads.
  Brian2 = the P1-3 results.

### Validation table (mean over 30 trials)

| Condition | Metric | Brian2 | PyTorch (± SE) | Δ | Criterion | Result |
|---|---|---|---|---|---|---|
| Baseline | MN9 / partner / active | 0 / 0 / 0 | 0 / 0 / 0 | — | exactly 0 | PASS |
| Sugar 200 Hz | MN9 (Hz) | 89.93 | 88.93 ± 0.74 | −1.1% | ±10% | PASS |
| | MN9 partner (Hz) | 62.83 | 62.40 ± 0.77 | −0.7% | ±10% | PASS |
| | active neurons | 395.0 | 390.7 | −1.1% | ±15% | PASS |
| Bitter 200 Hz | MN9 / partner (Hz) | 0 / 0 | 0 / 0 | — | exactly 0 | PASS |
| | active neurons | 83.4 | 82.9 | −0.6% | ±15% | PASS |
| Sugar + bitter | MN9 (Hz) | 6.80 | 6.73 ± 0.50 | −1.0% | ±10% | PASS |
| | MN9 partner (Hz) | 11.70 | 12.13 ± 0.55 | +3.7% | ±10% | PASS |
| | active neurons | 352.1 | 355.3 | +0.9% | ±15% | PASS |
| Pattern | bitter suppresses MN9 | 89.9 → 6.8 | 88.9 → 6.7 | — | lower | PASS |

Every difference is within about 1 SE (seed noise). Determinism
(`tests/test_determinism.py`): same seed → bit-identical counts and
20 ms bins; a different seed → different counts.

### Performance (this workstation: WSL2, x86, model already loaded)

Median of 5 runs. Drives: *sugar* = 20 sugar GRNs at 200 Hz (the
validated workload); *ORN* = left V + right DA2 ORNs at 100 Hz (56
ORNs, closest to a real hearing).

| Threads | Load (s) | Build (s) | Sugar 1 s | Sugar 2 s | ORN 1 s | ORN 2 s | Peak RSS |
|---|---|---|---|---|---|---|---|
| 1 | 0.29 | 0.34 | 4.75 s | 10.23 s | 8.54 s | **16.33 s** ✗ | 1.99 GB |
| **2** | 0.42 | 0.54 | 3.80 s | 8.86 s | 7.27 s | **13.05 s** ✓ | 1.98 GB |
| 4 | 0.43 | 0.48 | 3.68 s | 8.06 s | 8.75 s | 14.32 s ✓ | 1.98 GB |

- **Target (≤ 15 s per run, 1–2 s simulated):** met at 2 threads for
  every case. The worst case (ORN, 2 s) is 13.05 s, a margin of only
  about 13%.
- **Scaling:** 4 threads gains little, and loses on ORN, because the
  arrays are small (138k) and per-step overhead dominates. With no
  input at all a run still costs about 2.1 s per simulated second at
  2 threads (the P1-5 baseline condition), because every step touches
  every neuron.
- **Load times are warm-cache** (files in the OS page cache). Build is
  well under 1 s either way, so a worker can load once and reuse.
- **Caveat:** the production server is a 2-core **ARM** (Oracle
  Ampere); these numbers are x86. Re-measure there before relying on
  the margin.

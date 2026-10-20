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


## Steering probe (P1-6 risk check, pulls part of P1-8 forward)

**Question:** does argument text change which way the fly turns?
**Answer: no — not in the current model + readout.** Run 2026-10-20,
`SIM_VERSION` 0.2.0, 1 s per run, 1,446 runs (design B), 168 min wall
(6 workers × 2 threads; the Windows host throttled for part of it).
Code: `validation/steering_probe.py`, tables from
`validation/steering_report.py`, raw JSONL in
`sim/data/processed/validation/steering_*.jsonl`.

### Design

- **Per glomerulus:** all 47 antennal glomeruli (incl. V, DA2), ORNs of
  ONE side at 20 / 60 / 150 Hz per ORN (side-balanced like
  `smell.drives`), both sides, 3 seeds = 846 runs.
- **Readout:** DNa02 L/R rate, SI = (L − R)/(L + R) (SI > 0 = turn
  left; DNa02 is ipsilateral). **Toward score**
  T = (mean SI stimulating left − mean SI stimulating right) / 2; T > 0 =
  turns toward the stimulated side. "agree" = runs (of 6) whose
  per-run toward value has T's sign; **mirror** = mean SI(left stim) +
  mean SI(right stim) — 0 if mirror-symmetric.
- **Competition:** 5 X texts vs 5 Y texts through `smell.drives`, X left
  / Y right and swapped, 10 seeds = 500 runs. A **flip** = the same text
  wins in both orders (the winning side follows the text).
- **Low input:** the 5 matched pairs at ×0.1 rates = 100 runs.

### Finding 1 — the network is a switch, and its output ignores the side

Every run lands in one of two states:

- **Cascade** (658 / 846 runs): ~8,400–9,600 neurons active, and the
  DNs show one **fixed** pattern, identical whether the left or right
  antenna is driven (mean Hz, 545 cascade runs):

  | DN | L | R | stim-left L/R | stim-right L/R |
  |---|---|---|---|---|
  | DNa02 | 48.7 | 0.5 | 48.7 / 0.5 | 48.6 / 0.5 |
  | DNb05 | 195.5 | 171.0 | 195.1 / 170.3 | 196.0 / 171.8 |
  | DNg13 | 68.6 | 41.9 | 68.3 / 41.6 | 68.9 / 42.2 |
  | DNa01 | 18.7 | 7.3 | 18.6 / 7.4 | 18.9 / 7.2 |
  | DNb06 | 0.0 | 12.6 | 0.0 / 12.6 | 0.0 / 12.5 |
  | DNa04 | 2.5 | 0.0 | 2.4 / 0.0 | 2.5 / 0.0 |
  | DNa03, DNa11, DNp09, GF | 0 | 0 | — | — |

  So SI ≈ +1 (always "left") → mirror ≈ +2 and T ≈ 0 in the table below.
- **Quiet** (188 runs): ≤ 107 neurons active (median 22); **every DN
  silent**.
- **What triggers the cascade is glomerulus-specific and stochastic,
  not a level:** as little as DL2d's 7 ORNs at 20 Hz (140 input
  spikes/s) ignites it, while DA2 at 150 Hz (2,850 spikes/s), DA3 and
  DA4l never do. Quiet at mid rate: DA2, DA3, DA4l, DA4m, DL4, DM5, VA5,
  VA7m, VM2, VM5v. (Three of the aversive ones — DA2, DM5, DL4 — resist
  ignition: a valence hint in *whether* the brain lights up, not in
  turning.)
- **Not a wiring gap in DNa02:** the silent right DNa02 has slightly
  *more* net input than the left (751 vs 742 partners; net +3,571 vs
  +3,494 signed synapses). DNb05 and DNg13 inputs are also balanced. The
  left bias emerges from which upstream neurons are active in the
  cascade state.
- No Giant Fiber spikes in any run.

### Per-glomerulus table

| Glom | ORNs L/R | Letter | Lit. valence | T low | T mid | T high | SD mid | SNR mid | agree mid | mirror mid | active mid | GF Hz high | model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D | 16/15 | ע | aversive | +0.01 | -0.01 | -0.02 | 1.05 | 0.0 | 3/6 | +1.92 | 8376 | 0.0 | unclear |
| DA1 | 60/66 |  | — | -0.01 | +0.01 | +0.01 | 1.05 | 0.0 | 3/6 | +1.92 | 8440 | 0.0 | unclear |
| DA2 | 16/22 | ? | aversive | +0.00 | +0.49 | +0.33 | 0.54 | 0.9 | 3/6 | +0.98 | 4162 | 0.0 | unclear |
| DA3 | 14/16 | ח | neutral | +0.00 | +0.00 | +0.50 | 0.00 | inf | 0/6 | +0.00 | 15 | 0.0 | unclear |
| DA4l | 19/18 | כ | neutral | +0.00 | +0.00 | -0.49 | 0.00 | inf | 0/6 | +0.00 | 28 | 0.0 | unclear |
| DA4m | 20/19 |  | — | +0.00 | -0.14 | +0.00 | 0.94 | 0.1 | 3/6 | +1.59 | 6833 | 0.0 | unclear |
| DC1 | 21/18 | פ | neutral | +0.01 | +0.01 | +0.00 | 1.08 | 0.0 | 3/6 | +1.97 | 8371 | 0.0 | unclear |
| DC2 | 8/12 |  | — | +0.00 | +0.02 | -0.01 | 1.07 | 0.0 | 3/6 | +1.96 | 8371 | 0.0 | unclear |
| DC3 | 15/18 | ו | attractive | -0.03 | -0.01 | -0.01 | 1.08 | 0.0 | 3/6 | +1.98 | 8400 | 0.0 | unclear |
| DC4 | 11/11 | ז | aversive | +0.02 | +0.00 | +0.01 | 1.10 | 0.0 | 0/6 | +2.00 | 8391 | 0.0 | unclear |
| DL1 | 34/34 |  | — | -0.03 | +0.01 | -0.00 | 1.09 | 0.0 | 3/6 | +1.98 | 8426 | 0.0 | unclear |
| DL2d | 7/7 |  | — | -0.33 | -0.00 | -0.01 | 1.07 | 0.0 | 3/6 | +1.95 | 8397 | 0.0 | unclear |
| DL2v | 8/10 |  | — | -0.01 | -0.01 | +0.01 | 1.08 | 0.0 | 3/6 | +1.98 | 8368 | 0.0 | unclear |
| DL3 | 36/42 | ה | neutral | +0.00 | -0.01 | +0.01 | 1.09 | 0.0 | 3/6 | +1.98 | 8378 | 0.0 | unclear |
| DL4 | 27/25 | ר | aversive | +0.00 | -0.17 | +0.02 | 0.98 | 0.2 | 3/6 | +1.67 | 6718 | 0.0 | unclear |
| DL5 | 18/24 | ת | aversive | +0.01 | +0.01 | +0.01 | 1.09 | 0.0 | 3/6 | +1.99 | 8387 | 0.0 | unclear |
| DM1 | 35/33 | ד | attractive | +0.02 | -0.00 | -0.01 | 1.08 | 0.0 | 3/6 | +1.98 | 8437 | 0.0 | unclear |
| DM2 | 29/25 | ש | attractive | +0.02 | -0.01 | +0.00 | 1.08 | 0.0 | 3/6 | +1.98 | 8399 | 0.0 | unclear |
| DM3 | 32/29 |  | — | +0.01 | +0.01 | -0.01 | 1.08 | 0.0 | 3/6 | +1.97 | 8408 | 0.0 | unclear |
| DM4 | 20/20 |  | — | +0.01 | -0.01 | +0.00 | 1.07 | 0.0 | 3/6 | +1.96 | 8405 | 0.0 | unclear |
| DM5 | 21/21 | מ | aversive | +0.00 | -0.17 | +0.02 | 0.41 | 0.4 | 1/6 | +0.33 | 1387 | 0.0 | unclear |
| DM6 | 27/25 | נ | aversive | +0.00 | +0.01 | -0.00 | 1.07 | 0.0 | 3/6 | +1.95 | 8392 | 0.0 | unclear |
| DP1l | 12/12 |  | — | -0.01 | -0.01 | -0.01 | 1.06 | 0.0 | 3/6 | +1.93 | 8380 | 0.0 | unclear |
| DP1m | 16/16 |  | — | +0.01 | +0.00 | +0.01 | 1.07 | 0.0 | 3/6 | +1.95 | 8395 | 0.0 | unclear |
| V | 34/33 | ! | aversive | -0.49 | -0.01 | +0.03 | 1.07 | 0.0 | 3/6 | +1.96 | 8436 | 0.0 | unclear |
| VA1d | 48/45 | י | neutral | +0.00 | -0.01 | -0.01 | 1.08 | 0.0 | 3/6 | +1.97 | 8419 | 0.0 | unclear |
| VA1v | 46/38 | ק | neutral | +0.00 | -0.01 | +0.02 | 1.09 | 0.0 | 3/6 | +1.99 | 8419 | 0.0 | unclear |
| VA2 | 34/33 | ב | attractive | -0.00 | +0.03 | -0.00 | 1.06 | 0.0 | 3/6 | +1.94 | 8402 | 0.0 | unclear |
| VA3 | 13/13 | צ | neutral | +0.00 | +0.00 | +0.01 | 1.10 | 0.0 | 0/6 | +2.00 | 8356 | 0.0 | unclear |
| VA5 | 6/5 |  | — | +0.00 | +0.00 | -0.02 | 0.00 | inf | 0/6 | +0.00 | 10 | 0.0 | unclear |
| VA6 | 32/28 | א | aversive | +0.01 | +0.01 | +0.01 | 1.08 | 0.0 | 3/6 | +1.97 | 8407 | 0.0 | unclear |
| VA7m | 10/12 |  | — | +0.00 | +0.00 | +0.00 | 0.00 | inf | 0/6 | +0.00 | 18 | 0.0 | unclear |
| VC3 | 14/17 |  | — | -0.00 | +0.00 | +0.00 | 1.07 | 0.0 | 3/6 | +1.95 | 8396 | 0.0 | unclear |
| VC4 | 9/14 |  | — | +0.00 | -0.01 | -0.01 | 1.06 | 0.0 | 3/6 | +1.94 | 8381 | 0.0 | unclear |
| VC5 | 13/12 | ט | attractive | -0.02 | -0.01 | +0.01 | 1.07 | 0.0 | 3/6 | +1.95 | 8380 | 0.0 | unclear |
| VL1 | 39/39 |  | — | +0.00 | +0.00 | -0.01 | 1.08 | 0.0 | 3/6 | +1.97 | 8403 | 0.0 | unclear |
| VL2a | 33/38 | ג | attractive | +0.00 | +0.01 | +0.00 | 1.08 | 0.0 | 3/6 | +1.98 | 8415 | 0.0 | unclear |
| VL2p | 13/13 |  | — | +0.00 | +0.01 | +0.01 | 1.08 | 0.0 | 3/6 | +1.97 | 8390 | 0.0 | unclear |
| VM1 | 12/13 | ל | attractive | +0.33 | -0.01 | -0.01 | 1.09 | 0.0 | 3/6 | +1.99 | 8363 | 0.0 | unclear |
| VM2 | 19/18 | ס | neutral | +0.00 | +0.00 | -0.01 | 0.00 | inf | 0/6 | +0.00 | 28 | 0.0 | unclear |
| VM3 | 18/17 |  | — | -0.17 | +0.02 | -0.00 | 1.07 | 0.0 | 3/6 | +1.96 | 8367 | 0.0 | unclear |
| VM4 | 35/40 |  | — | -0.02 | -0.00 | +0.00 | 1.04 | 0.0 | 3/6 | +1.90 | 8414 | 0.0 | unclear |
| VM5d | 36/31 |  | — | +0.50 | +0.00 | -0.00 | 1.10 | 0.0 | 0/6 | +2.00 | 8440 | 0.0 | unclear |
| VM5v | 9/14 |  | — | +0.00 | +0.00 | +0.02 | 0.00 | inf | 0/6 | +0.00 | 29 | 0.0 | unclear |
| VM6l | 10/11 |  | — | +0.30 | -0.01 | +0.01 | 1.08 | 0.0 | 3/6 | +1.97 | 8343 | 0.0 | unclear |
| VM6m | 17/16 |  | — | +0.50 | +0.00 | -0.01 | 1.08 | 0.0 | 3/6 | +1.97 | 8379 | 0.0 | unclear |
| VM6v | 13/13 |  | — | +0.02 | +0.01 | -0.01 | 1.07 | 0.0 | 3/6 | +1.96 | 8392 | 0.2 | unclear |

### Literature valence vs model direction (mid rate)

| Literature \ model | toward | away | unclear |
|---|---|---|---|
| attractive | 0 | 0 | 7 |
| aversive | 0 | 0 | 9 |
| neutral | 0 | 0 | 8 |
| — | 0 | 0 | 23 |

### Candidate steering DNs (P1-4) vs DNa02

Mean toward score of each DN's own L/R index at mid rate, and in how
many glomeruli its sign matches DNa02's. All ≈ 0: no candidate DN
carries a side-dependent signal either.

| DN | mean toward (mid) | glomeruli agreeing with DNa02 sign |
|---|---|---|
| DNa01 | +0.01 | 24/47 |
| DNa03 | +0.00 | 0/47 |
| DNa04 | +0.00 | 9/47 |
| DNa11 | -0.00 | 1/47 |
| DNb05 | +0.00 | 20/47 |
| DNb06 | +0.01 | 0/47 |
| DNg13 | +0.00 | 24/47 |
| DNp09 | +0.00 | 0/47 |
| DNb02 | -0.07 | 14/47 |

### Competition (hearing-like: both antennas)

**Competition, full input**

| X (left first) | Y | X wins | flips | decided | mean SI XY | mean SI YX | active |
|---|---|---|---|---|---|---|---|
| x_att | y_att | 10/20 | 0/10 | 10/10 | +0.98 | +0.97 | 9527 |
| x_att | y_ave | 10/20 | 0/10 | 10/10 | +0.99 | +1.00 | 9528 |
| x_att | y_neu | 10/20 | 0/10 | 10/10 | +0.98 | +0.99 | 9520 |
| x_att | y_nat | 10/20 | 0/10 | 10/10 | +0.97 | +0.99 | 9572 |
| x_att | y_nat2 | 10/20 | 0/10 | 10/10 | +0.97 | +0.99 | 9566 |
| x_ave | y_att | 10/20 | 0/10 | 10/10 | +0.97 | +0.98 | 9538 |
| x_ave | y_ave | 10/20 | 0/10 | 10/10 | +0.97 | +0.98 | 9521 |
| x_ave | y_neu | 10/20 | 0/10 | 10/10 | +0.99 | +0.99 | 9509 |
| x_ave | y_nat | 10/20 | 0/10 | 10/10 | +0.97 | +0.99 | 9581 |
| x_ave | y_nat2 | 10/20 | 0/10 | 10/10 | +0.99 | +0.98 | 9558 |
| x_neu | y_att | 10/20 | 0/10 | 10/10 | +0.98 | +0.99 | 9523 |
| x_neu | y_ave | 10/20 | 0/10 | 10/10 | +0.97 | +0.98 | 9510 |
| x_neu | y_neu | 10/20 | 0/10 | 10/10 | +0.99 | +0.95 | 9483 |
| x_neu | y_nat | 10/20 | 0/10 | 10/10 | +0.98 | +0.98 | 9565 |
| x_neu | y_nat2 | 10/20 | 0/10 | 10/10 | +0.97 | +0.96 | 9547 |
| x_nat | y_att | 10/20 | 0/10 | 10/10 | +0.98 | +0.99 | 9618 |
| x_nat | y_ave | 10/20 | 0/10 | 10/10 | +0.98 | +0.98 | 9603 |
| x_nat | y_neu | 10/20 | 0/10 | 10/10 | +0.97 | +0.99 | 9582 |
| x_nat | y_nat | 10/20 | 0/10 | 10/10 | +0.99 | +0.99 | 9643 |
| x_nat | y_nat2 | 10/20 | 0/10 | 10/10 | +0.97 | +0.98 | 9637 |
| x_q | y_att | 10/20 | 0/10 | 10/10 | +1.00 | +0.97 | 9578 |
| x_q | y_ave | 10/20 | 0/10 | 10/10 | +0.98 | +0.98 | 9568 |
| x_q | y_neu | 10/20 | 0/10 | 10/10 | +0.97 | +0.98 | 9545 |
| x_q | y_nat | 10/20 | 0/10 | 10/10 | +0.98 | +0.98 | 9614 |
| x_q | y_nat2 | 10/20 | 0/10 | 10/10 | +0.99 | +0.97 | 9590 |

Flip rate: **0/250 = 0%** of decided (pair, seed) cases.

**Competition, x0.1 input**

| X (left first) | Y | X wins | flips | decided | mean SI XY | mean SI YX | active |
|---|---|---|---|---|---|---|---|
| x_att | y_att | 10/20 | 0/10 | 10/10 | +0.99 | +0.99 | 9069 |
| x_ave | y_ave | 10/20 | 0/10 | 10/10 | +0.96 | +0.99 | 9025 |
| x_neu | y_neu | 10/20 | 0/10 | 10/10 | +0.98 | +0.97 | 9099 |
| x_nat | y_nat | 10/20 | 0/10 | 10/10 | +0.97 | +0.98 | 9252 |
| x_q | y_nat2 | 10/20 | 0/10 | 10/10 | +0.96 | +0.97 | 9187 |

Flip rate: **0/50 = 0%** of decided (pair, seed) cases.

In all 300 competition runs SI ∈ [+0.86, +1.00]: **the text on the left
antenna always wins**, regardless of content. The ×0.1 level still
cascades (~9,000–9,250 active), so lowering the overall input does not
escape the global state (consistent with the P1-6 sanity probe down to
×0.02).

### Conclusions

- **No usable steering signal.** Turning direction is fixed by the
  network state, not by the stimulated side or the text; swap flip rate
  **0% (0/250 full, 0/50 at ×0.1)** vs the ≥ 75% exit criterion.
- **Literature valence is invisible in turning:** 0 of 24 mapped
  glomeruli turn the model consistently toward or away.
- Lower input does not help: either it still cascades (fixed output)
  or it stays quiet (no DN output at all).

## Sub-cascade readout probe (option 1)

**Question:** below the cascade threshold, is there a readout upstream of
the DNs that is side-dependent, graded and text-dependent?
**Answer: no. Below the threshold the brain does not respond at all.**
Run 2026-10-20, `SIM_VERSION` 0.2.0, 690 runs, 33 min. Code:
`validation/readout_probe.py`, `readout_report.py`,
`cascade_diagnostics.py`; raw data in
`sim/data/processed/validation/readout_*.jsonl`. No change to
`model.py`, `smell.py` or the mapping.

### 1. Cascade threshold with both antennas driven

Three hearing pairs (attractive, natural, aversive letter-sets), all
`smell.drives` rates × scale, 5 seeds each. Cascade = > 1,000 active.

| Scale | Input spikes/s (both antennas) | Cascades | Mean active | Max active |
|---|---|---|---|---|
| ×0.02 | 751 | 12/15 | 7,058 | 8,918 |
| ×0.01 | 375 | 10/15 | 5,817 | 8,741 |
| ×0.005 | 188 | 8/15 | 4,528 | 8,525 |
| ×0.002 | 75 | 0/15 | 74 | 134 |
| ×0.001 | 38 | 0/15 | 40 | 77 |
| ×0.0005 | 19 | 0/15 | 20 | 37 |

**Threshold: ×0.002 of `smell.py` rates ≈ 75 ORN spikes/s in total**
(≈ 0.06 Hz per ORN). Even there it isn't fully safe: 4 of the 500 swap
runs at ×0.002 (0.8%) still cascaded.

### 2–3. Candidate readouts at the threshold level

Pass criteria (fixed before running): (a) stimulated side > opposite in
≥ 90% of one-antenna runs; (b) stimulated-side activity strictly rises
over ¼ → ½ → 1 × threshold and is > 0 at ¼; (c) swap flip rate ≥ 75%
with ≥ 80% of the 250 (pair, seed) cases decided. Candidates: every
cell_class × hemisphere with both sides present (26 brain populations,
incl. uniglomerular and multiglomerular ALPNs, LHLN, LHCENT, ALLN,
Kenyon cells, MBON, DAN, mAL, CX, descending).

| Population | stim / opp (spikes) | side ok | ¼ → ½ → 1 | graded | flips | decided | verdict |
|---|---|---|---|---|---|---|---|
| olfactory (the input itself) | 38.2 / 0.0 | 100% | 9.5 → 19.6 → 38.2 | yes | 150/245 (61%) | 245/250 | reference only |
| all 26 brain populations | 0 / 0 | 0% | 0 → 0 → 0 | no | — | 0–4/250 | **fail** |

- In **586 of 590** sub-threshold runs **not a single non-ORN neuron
  spiked**. The only brain activity came from the 4 swap runs that
  cascaded.
- There is no graded middle regime: the brain is either silent or in
  the full cascade. No quiet run ever showed a handful of brain spikes,
  so the first downstream spike seems to set off the rest.
- Even a perfect readout of the input fails the text test (61% flips):
  at ~37 ORN spikes per antenna per second, Poisson noise swamps the
  difference between texts.

### 4. Control: a known lateralised circuit (sugar GRNs → MN9)

Annotation sugar GRNs (`cell_sub_class == "sugar"`, 20 L / 12 R), one
side at 200 Hz, 5 seeds.

| Sugar GRNs | MN9 L (spikes/s) | MN9 R (spikes/s) | ipsi / contra | active |
|---|---|---|---|---|
| left | 47.8 | 83.8 | 47.8 / 83.8 | 392 |
| right | 39.2 | 28.8 | 28.8 / 39.2 | 209 |

The gustatory circuit **does** lateralise: the dominant MN9 follows the
stimulated side (contralateral-dominant), the response is graded, and
4,000 input spikes/s never cascade. **The cascade is olfactory-specific.**

### Diagnostics: where does the cascade live?

`validation/cascade_diagnostics.py` rebuilds the model with edge subsets
(validation code only):

| Variant | Edge rows removed | Hearing active (2 seeds) | DM1 60 Hz L / R active | DL2d 20 Hz (2 seeds) | Sugar MN9 Hz |
|---|---|---|---|---|---|
| full | 0 | 9,605 / 9,674 | 8,467 / 8,415 | 8,373 / 14 | 87 / 66 |
| no synaptic input to ORNs | 66,603 | 9,404 / 9,413 | 7,981 / 7,978 | 7,945 / 14 | 87 / 66 |
| no KC → KC | 293,762 | 9,104 / 9,081 | 7,871 / 7,887 | 7,811 / 14 | 87 / 66 |

- Neither ORN axo-axonal input nor KC→KC excitation causes the cascade;
  the runaway is in the central olfactory network.
- The network has high gain and no brake: in Shiu's LIF a single
  presynaptic spike fires a target through ≥ 162 synapses (peak factor
  0.157); **1,914** edges are that strong, **12,884** fire with 2
  coincident spikes, **29,414** with 3. The model has no short-term
  depression and no spike-frequency adaptation.

### Verdict

**No readout passes.** Below the threshold there is nothing to read;
above it the output is fixed. ORN adaptation alone can't fix this. Any
input-side mechanism only moves the operating point along the same
silent ↔ cascade axis: even a 500× cut still cascades 0.8% of the
time. And removing ORN input synapses did not prevent the cascade.
The option 2 plan therefore targets central dynamics; see DECISIONS.md
2026-10-20 "Option 2 plan".

## Prototypes A (ORN→PN depression) and B (taste of words)

Run 2026-10-20, validation code only (`validation/std_model.py`,
`taste.py`, `proto_probe.py`, `proto_report.py`); no change to
`model.py`, `smell.py` or the mapping. Raw data:
`sim/data/processed/validation/proto_*.jsonl`. Pass criteria as in the
sub-cascade probe: one direction (ipsi or contra) in ≥ 90% of one-side
runs, graded over the levels, swap flip rate ≥ 75% with ≥ 80% decided.
The driven input class is shown for reference only.

**Runtime note:** the estimate was ~20 min; actual ~70 min of compute
plus ~25 min lost to a fork deadlock I introduced (torch ops in the
parent before forking workers — fixed with NumPy) and to stuck
processes. STD runs in the cascade state were ~4 min each per worker,
so A was cut short once its gate result was clear (below).

### Prototype A — short-term depression on ORN→PN synapses only

Resource model on the 19,438 ORN→ALPN synapse rows: a spike delivers
`w·x` (an isolated spike keeps the validated weight), then
`x ← x·(1 − U)`; recovery `x → 1` with τ_rec. Checked: U = 0 reproduces
the base model exactly (84,060 = 84,060 spikes).

- **A1 (primary): U = 0.22, τ_rec = 893 ms** — Nagel, Hong & Wilson
  2015 (*Nat Neurosci* 18:56), fit of the whole ORN→PN EPSC at 10 Hz:
  f = 0.78, τ = 893 ms. Kazama & Wilson 2008 give strong depression
  above ~50 spikes/s and release probability p = 0.79 ± 0.02 (Fig. 5C)
  but no recovery constant.
- **A2 (upper bound): U = 0.79** (Kazama & Wilson's p used as depletion
  per spike), τ_rec = 893 ms.

| Run set | Runs | Active neurons | DNa02 L/R (Hz) | uPN spikes L / R | Result |
|---|---|---|---|---|---|
| A1 one antenna, ×0.1 / ×0.3 / ×1 | 12 | 8,756 → 8,858 | ~50 / ~0 for every side | ~17.8k / ~16.2k for both stimulated sides | runaway, no side signal, not graded |
| A1 hearings (x_att vs y_att, both orders) | 6 | 9,322–9,382 | ~50 / ~0 | — | SI +0.93…+1.00 in both orders: 0/3 flips |
| A2 one antenna, ×0.1 / ×1 | 4 | 8,760–8,852 | 46–57 / 0–3 | 17.7–18.0k / 16.1–16.5k for both sides | runaway persists |

**A fails the gate:** depression at ORN→PN, even at the strongest
bound, does not stop the runaway or create any side signal — consistent
with the diagnostics placing the runaway in the central network. The
remaining A swap runs were not run.

### Prototype B — taste of words

**1. GRN inventory (v783, in model, by organ = nerve):**

| GRN class | Organ (nerve) | L | R |
|---|---|---|---|
| sugar (LB3c) | labellum (MxLbN) | 20 | 12 |
| sugar/low_salt (LB3b) | labellum | 13 | 12 |
| water (LB3a) | labellum | 15 | 15 |
| putative_attractive (LB4a, LB4b) | labellum | 6 | 8 |
| bitter (LB1a–d) | labellum | 21 | 21 |
| high_salt/heavy_metal (LB3d) | labellum | 15 | 14 |
| putative_aversive (LB2a–c) | labellum | 7 | 8 |
| glutamate (LB1e) | labellum | 11 | 12 |
| taste peg (claw_tpGRN, dorsal_tpGRN) | labellum | 37 | 36 |
| leg GRNs (SA_VTV_pro_meso_meta, LgAG1–9) | legs (cervical connective) | 37 | 37 |
| pharyngeal groups 1–3 (PhG7–9) | pharynx (PhN) | 6 | 6 (one side each per group) |
| accessory pharyngeal (PhG1–16) | pharynx (aPhN) | 18 | 20 |

**2. Diversity and mapping scheme.** Enough, if classes are split by
cell type and the large ones in half (by root_id): 24 groups with ≥ 2
GRNs per side, each letter keeping its valence from `smell.LETTERS`.

| Key | GRN group | GRNs | | Key | GRN group | GRNs |
|---|---|---|---|---|---|---|
| ! | bitter LB1a | 16 | | ת | bitter LB1c (½) | 6 |
| ? | high-salt LB3d | 29 | | נ | bitter LB1c (½) | 5 |
| ד | sugar/low-salt LB3b | 25 | | א | putative aversive LB2a | 4 |
| ב | sugar LB3c (½) | 16 | | ז | putative aversive LB2b | 4 |
| ש | sugar LB3c (½) | 16 | | י | taste peg claw_tpGRN | 60 |
| ו | water LB3a (½) | 16 | | ה | leg LgAG1 | 25 |
| ל | water LB3a (½) | 14 | | כ | glutamate LB1e | 23 |
| ט | putative attractive LB4b | 10 | | ח | leg LgAG2 | 12 |
| ג | putative attractive LB4a | 4 | | ק | taste peg dorsal_tpGRN | 11 |
| מ | bitter LB1d | 8 | | פ | leg LgAG4 | 8 |
| ר | bitter LB1b | 7 | | ס | leg LgAG8 | 8 |
| ע | putative aversive LB2c | 7 | | צ | leg LgAG3 | 6 |

דבש → the sugar groups. Weak points: several aversive groups have only
2–3 GRNs per side; the pharyngeal GRNs are too unilateral to use.

**3–4. Test** (rates from `smell.glomerulus_rates`, side-balanced; one
side at ¼ / ½ / 1×, 3 texts × 5 seeds = 90 runs; swap on 10 pairs — the
5 matched + 5 valence-cross pairs — both orders, 10 seeds = 200 runs).

- **Runaway: yes, sometimes** — 37 / 290 runs (13%) exceeded 4,000
  active (max 9,110), mostly right-side or both-side drives at ½–1×;
  median active 762.
- **Text and valence reach the brain:** with the attractive set on one
  side, MN9 rises 1.8/2.8 → 27/37 → 47/64 spikes/s over ¼ → ½ → 1×;
  with the aversive set MN9 stays at 0 at every level — the first
  valence-dependent output we have seen.
- **But no lateralised brain readout passes:**

| Readout | direction | side ok | levels (dominant side) | graded | flips | decided | verdict |
|---|---|---|---|---|---|---|---|
| gustatory (the input itself) | ipsi | 100% | 1337 → 2657 → 5281 | yes | 80/100 (80%) | 100/100 | reference only |
| AN (ascending neurons) | ipsi | 100% | 37 → 109 → 243 | yes | 58/97 (60%) | 97/100 | fail |
| MN9 | contra | 43% | 1.4 → 10.1 → 18.7 | yes | 40/75 (53%) | 75/100 | fail |
| descending (all DNs) | ipsi | 97% | 20 → 156 → 569 | yes | 40/100 (40%) | 100/100 | fail |
| central | ipsi | 83% | 178 → 1272 → 7671 | yes | 38/100 (38%) | 100/100 | fail |
| brain_motor_neuron | contra | 37% | 7.6 → 80 → 199 | yes | 5/89 (6%) | 89/100 | fail |
| DNa02 | contra | 23% | 0 → 0.8 → 5.9 | no | 0/39 (0%) | 39/100 | fail |

  (Full table: `PYTHONPATH=src uv run python -m validation.proto_report b`.)

### Verdict

| | A: ORN→PN depression | B: taste of words |
|---|---|---|
| Runaway | **yes**, every run (A1 and A2) | **sometimes**: 13% of runs |
| Side signal | none (identical L/R output either side) | yes in ascending/descending totals (ipsi 97–100%); MN9 weak (43%) |
| Graded | no (8,760 → 8,858 active over 10×) | yes (MN9, AN, DNs grow with input) |
| Text / valence | none | yes: attractive drives MN9, aversive silences it |
| Swap flip rate | 0/3 (SI ≈ +1 in both orders) | best brain readout 60% (AN), MN9 53%, DNs 40% — below 75% |
| Model change | new synapse dynamics in `model.py` + Brian2 port, re-validation | none to the model; new input module replacing `smell.py`; SPEC change |

Neither passes. B is the only path where text and valence measurably
reach the brain without changing the validated model.

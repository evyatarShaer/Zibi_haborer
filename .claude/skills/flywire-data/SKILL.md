---
name: flywire-data
description: Use whenever code loads, queries, or references the FlyWire connectome — neuron tables, synapse edges, neurotransmitter predictions, soma positions, or any specific neuron/GRN group IDs. Keeps dataset version, file layout, and canonical IDs consistent across the simulator.
---

# flywire-data

Anything that touches the connectome goes through this skill. Every
fact below was verified against the loaded v783 data (P1-4,
2026-10-20); `sim/tests/test_data.py` and `test_anatomy.py` pin them.

## Dataset

- **Version:** FlyWire **v783** (pinned). Any upgrade bumps `SIM_VERSION`
  and is logged in `docs/DECISIONS.md`.
- **Raw files:** `sim/data/raw/flywire_v783/` (gitignored). URLs,
  sha256 and full dtypes: `docs/DATA_SOURCES.md`.
- **Processed:** `sim/data/processed/` (gitignored) — no derived tables
  yet. There is no `neurons.parquet` / `connections.parquet`.

## The three raw files

| File | Rows | Columns used |
|---|---|---|
| `Completeness_783.csv` | 138,639 | `Unnamed: 0` = root_id (row order = **model index**), `Completed` |
| `Connectivity_783.parquet` | 15,091,983 | `Presynaptic_Index`, `Postsynaptic_Index` (model indices), `Excitatory x Connectivity` (signed synapse count). Also `Presynaptic_ID`, `Postsynaptic_ID`, `Connectivity` (count), `Excitatory` (±1). **No NT string column.** |
| `Supplemental_file1_neuron_annotations.tsv` | 139,248 | `root_id`, `cell_type`, `side`, `super_class`, `cell_class`, `cell_sub_class`, `nerve`, `top_nt`, `hemibrain_type`, `soma_x/y/z`, `pos_x/y/z` (+ 17 more) |

- 623 annotated neurons are **not** in the model (not in Completeness);
  2 of them are ORNs. Selections drop them.
- `side` values: `left` / `right` / `center` / `na` (literal string).

## What the code exposes

- `borer_sim.data` — the **only** loader (cached per process):
  `neuron_ids()` (Index of root_ids, position = model index),
  `connectivity()` (the three model columns), `annotations()` (indexed
  by root_id), `to_index(root_ids)` (→ model indices; KeyError if any
  id is not in the model).
- `borer_sim.anatomy` — named sets, filtered at runtime, returned as
  **sorted model indices**: `cell_type(name, side)`, `mn9(side)`,
  `giant_fiber(side)`. Root_id for an index: `data.neuron_ids()[idx]`.
- `borer_sim.taste` — GRN groups and the letter table: `grns()` (GRN
  annotation rows), `groups()` (name → root_ids), `mapping()` (letter /
  mark → group), `drives()` / `tasting()` (Poisson input).

## Side convention (critical for any left/right selection)

**Annotation `side` is the fly's own side** (soma hemisphere, fly's
perspective). Use it as the source of truth; never mix in side labels
from older papers/code. Evidence:

1. **FlyWire docs:** FAFB was imaged left/right inverted; FlyWire
   inverted all side labels to fix it (images untouched). The fafbseg
   docs: "the official `side` labels … are biologically correct" and in
   a frontal image view "image left" is the fly's left.
2. **Coordinates agree:** `side == "left"` somas sit at low x (n=58,611,
   median `soma_x` 77,736, max 136,224); `side == "right"` at high x
   (n=59,395, median 183,856, min 123,632). Only 0.004% of left somas
   lie above the global median → labels follow hemispheres cleanly,
   with low x = image left = fly's left.
3. **Pre-correction labels are mirrored:** all of Shiu 2024's (v630)
   "right" sugar GRNs are `side == "left"` here, and his "left" MN9 is
   `side == "right"` — exactly the documented label inversion.
4. **Asymmetric body (suggestive, not decisive):** the two most
   lateralized central types are the hemibrain AB types — `SA1` 0 L /
   12 R, `SA2` 9 L / 0 R. Confirming which one fills the larger (right)
   AB needs per-neuropil synapses, which we don't have.

## Canonical lookups (filters; IDs for reference only)

- **GRNs (taste input):** `cell_class == "gustatory"` → 410, all in
  the model, 206 L / 204 R (none `center`/`na`). Sub-classes (GRNs):
  SA_VTV_pro_meso_meta (legs, LgAG1–9) 74, taste peg 73, bitter (LB1a–d)
  42, accessory_pharyngeal_nerve_sensory_group1 (PhG*) 36, sugar (LB3c)
  32, water (LB3a) 30, high_salt/heavy_metal (LB3d) 29, sugar/low_salt
  (LB3b) 25, glutamate (LB1e) 23, putative_aversive (LB2a–c) 15,
  putative_attractive (LB4a–b) 14, pharyngeal groups 1–3 + accessory
  group2 14. Nerve: `MxLbN` 286 (labellum), `CV` 74 (legs), `aPhN` 38,
  `PhN` 12.
- **GRN groups** (`taste.groups()`): one per `cell_sub_class` ×
  `cell_type` with ≥ 2 GRNs on each side → 24 groups, plus halves
  `/a` `/b` of `sugar:LB3c` and `high_salt/heavy_metal:LB3d` (per side,
  sorted by root_id, dealt alternately) = 28. **Excluded** (ignite the
  runaway alone at 150 Hz, > 4,000 active): `sugar/low_salt:LB3b` (3/3
  seeds, ~8.5k active) and `SA_VTV_pro_meso_meta:LgAG3` (2/3, ~8.4k).
  Pharyngeal groups are too one-sided to qualify.
- **MN9 (verdict readout):** `cell_type == "CB0701"` → 1 per side,
  `brain_motor_neuron`, acetylcholine. Left `720575940618238523`, right
  `720575940660219265` (Shiu's v630 "left" `id_mn9` = side right here).
- **Giant Fiber (DNp01):** `cell_type == "DNp01"` (`hemibrain_type ==
  "Giant Fiber"` confirms) → 1 per side. Left `720575940622838154`,
  right `720575940632499757`. Note: predicted NT differs between them
  (left acetylcholine, right glutamate).
- **Soma positions:** `soma_x`, `soma_y`, `soma_z` on `annotations()`
  (NaN for ~21k neurons; `pos_x/y/z` is always set).

## Rules

- **Never hard-code a root_id or column name without verifying it
  against the loaded data in a notebook or test.** IDs above are for
  reference; code selects by filter through `anatomy`.
- **All loads happen through `borer_sim.data`** — no ad-hoc reads.
- **Load into memory once per worker** (`data` caches).
- **Determinism.** Any derived table must be reproducible from the raw
  files + a seed + `SIM_VERSION`. Selections return sorted indices.
- **License.** CC BY-NC 4.0 — non-commercial only (DECISIONS.md).

## Where this gets used

- `sim/src/borer_sim/data.py` — the single loader.
- `sim/src/borer_sim/anatomy.py` — named neuron sets.
- `sim/src/borer_sim/model.py` — builds the sparse weight matrix (P1-5).
- `sim/src/borer_sim/taste.py` — letters → GRN groups (P1-6).
- `sim/src/borer_sim/readout.py` — MN9, Giant Fiber (P1-8, not yet).

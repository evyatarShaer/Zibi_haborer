---
name: flywire-data
description: Use whenever code loads, queries, or references the FlyWire connectome — neuron tables, synapse edges, neurotransmitter predictions, soma positions, or any specific neuron/glomerulus IDs. Keeps dataset version, file layout, and canonical IDs consistent across the simulator.
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
  **sorted model indices**: `cell_type(name, side)`,
  `orns(glomerulus, side)`, `turning_dns(side)`, `giant_fiber(side)`,
  `orn_glomeruli()` (counts per glomerulus × side + entry nerve).
  Root_id for an index: `data.neuron_ids()[idx]`.

## Side convention (critical for the turning readout)

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

- **ORNs:** `cell_type == "ORN_<glomerulus>"` and `side`. All are
  `super_class == "sensory"`, `cell_class == "olfactory"`. 53 glomeruli,
  1,114 L / 1,132 R in-model ORNs (+ 29 with `side == "na"`, excluded).
  Entry nerve: `AN` (antenna) except palp glomeruli **VA4, VA7l, VC1,
  VC2, VM7d, VM7v** (`MxLbN`, maxillary palp; VA4 has 1 AN ORN).
- **CO₂ (V):** `orns("V", side)` → 34 L / 33 R.
- **Geosmin (DA2):** `orns("DA2", side)` → 16 L / 22 R (+1 `na`).
- **Turning DN (DNa02):** `cell_type == "DNa02"` → 1 per side.
  Left `720575940629327659`, right `720575940604737708`.
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
- `sim/src/borer_sim/readout.py` — turning DNs, Giant Fiber (P1-8).
- `sim/src/borer_sim/smell.py` — letters → glomerulus ORN sets (P1-6).

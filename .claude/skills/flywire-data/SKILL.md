---
name: flywire-data
description: Use whenever code loads, queries, or references the FlyWire connectome — neuron tables, synapse edges, neurotransmitter predictions, soma positions, or any specific neuron/glomerulus IDs. Keeps dataset version, file layout, and canonical IDs consistent across the simulator.
---

# flywire-data

Anything that touches the connectome goes through this skill.

## Dataset

- **Version:** FlyWire **v783** (pinned). Any upgrade bumps `SIM_VERSION`
  and is logged in `docs/DECISIONS.md`.
- **Raw files:** `sim/data/raw/` (gitignored).
- **Processed Parquet:** `sim/data/processed/` (gitignored).

## Expected processed tables (fill exact schemas after download)

- `neurons.parquet` — one row per neuron.
  Columns (verify): `root_id` (int64), `cell_type`, `super_class`,
  `side` (`left`|`right`|`center`), `nt_type` (predicted
  neurotransmitter), `soma_x`, `soma_y`, `soma_z`.
- `connections.parquet` — one row per directed edge.
  Columns (verify): `pre_root_id`, `post_root_id`, `syn_count`,
  `nt_type` (inherited from pre).
- `annotations.parquet` — human-curated labels where available.

## Canonical lookups (fill once discovered — never guess)

Record real column names and IDs here as they're verified against the
data. Until verified, mark `TBD`.

- **Olfactory receptor neurons (ORNs) by glomerulus and side:**
  - Column(s) used: `TBD`
  - Example filter: `TBD`
- **CO₂ glomerulus (V) ORNs:** `TBD`
- **Geosmin glomerulus (DA2) ORNs:** `TBD`
- **Turning descending neurons (DNa02 family — verify):**
  - Left DNa02 root_ids: `TBD`
  - Right DNa02 root_ids: `TBD`
- **Giant Fiber (DNp01 — verify):**
  - root_id(s): `TBD`
- **Soma positions:** `soma_x`, `soma_y`, `soma_z` on `neurons.parquet`
  (verify column names).

## Rules

- **Never hard-code a root_id or column name without verifying it
  against the loaded data in a notebook or test.** If you find yourself
  guessing, stop and open the data first.
- **All loads happen through a single `data.py` module** — no ad-hoc
  reads scattered across the codebase.
- **Load into memory once per worker.** The full connectome fits in
  RAM; repeated Parquet reads waste wall-clock.
- **Determinism.** Any computed derived table (e.g. subcircuit) must be
  reproducible from the raw files + a seed + `SIM_VERSION`.
- **License.** FlyWire data terms must be checked before any
  commercial launch (open question in `docs/DECISIONS.md`).

## Where this gets used

- `sim/src/borer_sim/data.py` — the single loader.
- `sim/src/borer_sim/model.py` — builds the sparse weight matrix.
- `sim/src/borer_sim/readout.py` — selects turning DNs and the Giant
  Fiber.
- `sim/src/borer_sim/smell.py` — maps letters to glomerulus-specific
  ORN sets.

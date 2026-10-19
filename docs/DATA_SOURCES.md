# Data sources (Phase 1 — POC)

> Research notes for task **P1-2**. Nothing has been downloaded yet.
> Download only after the user approves this file.

## Scope

For the POC we need the minimum data to:
1. Reproduce one Shiu et al. 2024 result (validation).
2. Build a whole-brain LIF model on FlyWire **v783**.
3. Select ORNs by glomerulus and side, the DNa02 turning pair, and the
   Giant Fiber (DNp01) by name — i.e. we need cell-type annotations.

That requires exactly three data files. Everything else is deferred.

## Dataset version

- **FlyWire release:** `783` (pinned in `docs/DECISIONS.md`).
- **Annotations repo tag:** latest `main` (currently covers v783; use
  tag `v2.1.0` if we need the exact Schlegel et al. 2024 Nature state).

## License summary (critical)

- **FlyWire v783 connectome data:** **CC-BY-NC 4.0** — attribution,
  **non-commercial** only. Confirmed by multiple downstream repos and
  the FlyWire citation guidelines. The current product is non-commercial
  (Vercel Hobby), so this is fine; a commercial launch would require
  a separate license from Princeton/FlyWire.
- **Shiu et al. code (`philshiu/Drosophila_brain_model`):** MIT (code
  only). The data files vendored in that repo are derived from FlyWire
  v783 and therefore inherit **CC-BY-NC 4.0**.
- **Annotations (`flyconnectome/flywire_annotations`):** derived from
  FlyWire v783 → inherits **CC-BY-NC 4.0**. No separate LICENSE file in
  the repo; attribution requirement = cite Schlegel et al. 2024,
  Dorkenwald et al. 2024.
- This resolves the "FlyWire license" open question in
  `docs/DECISIONS.md §13` **for non-commercial use only**. The
  commercial-launch question stays open.

## Files to download for Phase 1

All three downloads are over plain HTTPS, no login, no API key.

### 1. `Connectivity_783.parquet` — thresholded edge list with NT

- **URL:** https://raw.githubusercontent.com/philshiu/Drosophila_brain_model/main/Connectivity_783.parquet
- **Size:** **96.1 MB** (100,804,642 bytes)
- **Format:** Parquet
- **Login:** none
- **License:** CC-BY-NC 4.0 (data) / MIT (containing repo)
- **Purpose:** directed edges (`pre_root_id`, `post_root_id`,
  `syn_count`, `nt_type`) used to build the sparse weight matrix for
  the LIF model. This is the FlyWire v783 build Shiu publishes as a
  drop-in for his model.
- **Destination:** `sim/data/raw/flywire_v783/Connectivity_783.parquet`

### 2. `Completeness_783.csv` — complete neuron list for v783

- **URL:** https://raw.githubusercontent.com/philshiu/Drosophila_brain_model/main/Completeness_783.csv
- **Size:** **3.17 MB** (3,327,347 bytes)
- **Format:** CSV
- **Login:** none
- **License:** CC-BY-NC 4.0 (data) / MIT (containing repo)
- **Purpose:** the authoritative list of neuron `root_id`s in v783 that
  Shiu's model uses; aligns with `Connectivity_783.parquet`.
- **Destination:** `sim/data/raw/flywire_v783/Completeness_783.csv`

### 3. `Supplemental_file1_neuron_annotations.tsv` — cell types + NT

- **URL:** https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/supplemental_files/Supplemental_file1_neuron_annotations.tsv
- **Size:** **30.3 MB** (31,720,298 bytes)
- **Format:** TSV
- **Login:** none
- **License:** CC-BY-NC 4.0 (derived from FlyWire v783)
- **Purpose:** per-neuron metadata (`root_id`, `super_class`,
  `cell_class`, `cell_type`, `side`, `top_nt`, `top_nt_conf`, `soma_x/y/z`,
  `nerve`, hemilineage, synonyms). This is how we resolve names like
  **DNa02**, **DNp01 / Giant Fiber**, **ORN_V** (CO₂), **ORN_DA2**
  (geosmin) to actual root_ids for use in `smell.py` and `readout.py`.
- **Destination:** `sim/data/raw/flywire_v783/Supplemental_file1_neuron_annotations.tsv`

### Reference code (not data) — Shiu et al. 2024

- **Repo:** https://github.com/philshiu/Drosophila_brain_model
- **Files we read for the P1-3 baseline:** `model.py`, `utils.py`,
  `example.ipynb`. MIT, tiny.
- **Paper:** Shiu et al., *Nature* 634, 210–219 (2024).
  DOI: 10.1038/s41586-024-07763-9.
- Not downloaded as a dataset — we clone or vendor the files we actually
  need under `sim/references/` later if required.

## Explicitly NOT downloading in Phase 1

- **Full FlyWire v783 synapse table** (per-synapse positions,
  neuropils): Zenodo record `10676866`. Multi-GB. Needed only for the
  3D animation in Phase 2.
- **Shiu online archive** of pre-computed model outputs:
  DOI `10.17617/3.CZODIW`. Several GB. We compute our own runs.
- **Legacy v630 files** in Shiu's repo (`2023_03_23_*`). We pinned v783.
- **FlyWire Codex direct exports** (`codex.flywire.ai/api/download`).
  Requires Google sign-in. The three files above cover everything we
  need without that.

## Total download for Phase 1

**~130 MB** (96.1 + 3.17 + 30.3).

Well under the 1 GB "stop and ask" threshold in `CLAUDE.md`, but the
user has asked to review this file before any download starts.

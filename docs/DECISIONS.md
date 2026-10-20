# Decisions log

Record every non-obvious decision. Append — don't rewrite history.

**Format:**
```
## YYYY-MM-DD — Short title
**Context:** what we were deciding and why.
**Decision:** the choice.
**Why:** reasoning.
**Alternatives considered:** what we rejected.
**Impacts:** files, phases, or decisions affected.
```

---

## 2026-10-19 — Initial stack and architecture (free-only)

**Context:** Need to pick a stack that stays within free tiers through MVP
and allows a path to commercial use later.

**Decision:**
- Sim in Python 3.12 + PyTorch sparse.
- API: FastAPI.
- Queue: Postgres `SKIP LOCKED` (no Redis).
- DB: Neon Postgres free tier.
- Frontend: Next.js + Tailwind on Vercel Hobby.
- Files: Cloudflare R2 free tier.
- API/worker host: Oracle Cloud Always Free ARM (2 OCPU / 12 GB). Beta
  fallback: worker on home PC.
- Analytics: PostHog free tier.

**Why:** Everything above has a free tier with no time-limited trial.
Vercel Hobby is explicitly non-commercial — the moment this earns money
we must upgrade (noted here so we don't forget).

**Alternatives considered:** Redis for queue (adds a service for no
benefit at this scale); Fly.io (free tier removed); AWS Lambda (cold
starts hurt the hearing UX).

**Impacts:** `docs/SPEC.md §11`, Phase 2 scaffold.

---

## 2026-10-19 — No AI in the product's decision path

**Context:** We *could* easily use an LLM to score arguments. Deliberately
rejecting that.

**Decision:** No AI/LLM in the decision, verdict text, or moderation.
Using an AI to *write code* is fine.

**Why:** The fly deciding is the premise. LLM scoring would make it a
different (and more boring) product.

**Alternatives considered:** LLM as a secondary "humor layer" that
rewrites template sentences — rejected; templates are human-written.

**Impacts:** all phases.

---

## 2026-10-19 — FlyWire dataset version pinned to v783

**Context:** FlyWire releases new versions periodically; deterministic
reruns require a pinned version.

**Decision:** Pin to **v783** for POC and MVP. Any upgrade bumps
`SIM_VERSION`.

**Why:** v783 is the version used in Shiu et al. 2024 — matches our
reference implementation.

**Impacts:** `.claude/skills/flywire-data`, `SIM_VERSION`.

---

## Open questions (to resolve during POC)

- Letter → glomerulus mapping table and attractive / aversive / neutral
  balance.
- Numerical thresholds: gap for a decisive win (currently 5%), flips for
  "dithered" (3), hunger for "went for food" (0.8).
- FlyWire data license terms for commercial use — read before any
  commercial launch.
- Publish mapping table openly, or let players discover it by playing?

---

## 2026-10-19 — Measurable POC exit criteria, gap definition, determinism scope

**Context:** Review of the spec found that "side A wins ~50%" passes even
if the fly always turns left (side→antenna is a coin flip), "different
texts → different verdicts" wasn't measurable, `gap` was never defined,
and bit-identical results can't be guaranteed across CPU architectures
(home PC x86 vs. Oracle ARM).

**Decision:**
- Balance: side A **and** left antenna each win 45–55% over 1,000 pairs.
- Swap test: 200 pairs, (X vs Y) then (Y vs X) with identical seed, mood
  and antenna assignment → winner flips in ≥ 75% of decided cases.
- Outcome mix: Win ≥ 50%; each special outcome ≤ 15%.
- `margin = max(A,B)/(A+B)`, `gap = 2·margin − 1`.
- Determinism promised per platform only. Runs are computed once and
  stored; `Run.platform` added.
- Hunger rate stays +0.1/h on purpose: after ~8 h a close case becomes
  "went for food" (a late side starves the fly).

**Why:** Turn vague criteria into numbers the phase gate can check.

**Alternatives considered:** Swap-flip threshold 70% or 80%; slowing
hunger to +0.05/h — both rejected for now, revisit after POC data.

**Impacts:** `docs/SPEC.md` §2, §5, §6, §7, §10, §12; `docs/TASKS.md`;
`CLAUDE.md`; `.claude/skills/sim-change`.

---

## 2026-10-19 — Project moved into WSL filesystem

**Context:** During P1-1 verification the smoke tests in `sim/` took
**233 s** when the repo lived on the Windows Desktop
(`/mnt/c/Users/evyatar 2/Desktop/Zibi_haborer`) and we ran `uv run
pytest -q` through WSL. The cause is well-known cross-filesystem I/O
cost on `/mnt/c` — every file read in `.venv` crosses the 9P boundary.

**Decision:** The canonical working copy of the project now lives at
`~/projects/Zibi_haborer` **inside the WSL2 Ubuntu filesystem**. All
development — Claude Code sessions, `git`, `uv`, pytest, future data
downloads under `sim/data/raw/` — happens there. The Desktop copy is
kept as a stale backup; it will not be edited and will not receive
future commits.

**Why:** After moving the repo into the native ext4 filesystem the
same `uv run pytest -q` runs in **9.08 s** (~26× faster). Keeping data
and the virtualenv on `/mnt/c` would make Phase 1 unworkable once we
load the ~130 MB FlyWire v783 tables.

**Alternatives considered:**
- Leave the repo on Desktop and only move `.venv` and `sim/data/`
  into WSL — rejected: splits the tree, breaks git hygiene, and
  `uv sync` would re-fetch cross-FS anyway.
- Use a Windows-native Python toolchain — rejected: Shiu's model and
  Brian2 are far better supported on Linux, and the production host
  (Oracle ARM) is Linux.

**Impacts:** `CLAUDE.md` Platform rule rewritten. Credentials in WSL
now go through Windows Git Credential Manager
(`"/mnt/c/Program Files/Git/mingw64/bin/git-credential-manager.exe"`)
so the GitHub token is shared with the Windows install.

---

## 2026-10-19 — Non-commercial use only (FlyWire CC BY-NC 4.0)

**Context:** P1-2 downloaded the FlyWire v783 data (connectivity,
completeness, annotations). flywire.ai/guidelines states the public
release data is licensed **CC BY-NC 4.0**; the Shiu and
flyconnectome files are derived from it and inherit the same terms.

**Decision:** HaBorer is **non-commercial only** until a separate
license is obtained from Princeton/FlyWire. No ads, payments,
sponsorships or other revenue while it runs on FlyWire data. Required
attribution and citations live in `README.md` → "Data & license" and
must also appear in the product's About/credits page (Phase 2).

**Why:** Using CC BY-NC data commercially would breach the license.
The current stack is already non-commercial (Vercel Hobby), so this
costs nothing now.

**Alternatives considered:** Seek a commercial license now — premature
before the POC proves the idea works. Replace FlyWire with another
connectome — none with comparable whole-brain coverage.

**Impacts:** `README.md`, `docs/DATA_SOURCES.md`. Resolves the FlyWire
license open question for non-commercial use; the commercial-launch
question stays open (license required first).

---

## 2026-10-19 — `borer_sim.data`: single v783 loader (SIM_VERSION 0.0.2)

**Context:** P1-3 needs the connectome in a model; the flywire-data
skill requires every load to go through one `data.py`.

**Decision:** Add `sim/src/borer_sim/data.py` — cached loaders
`neuron_ids()` (Completeness order = model index), `connectivity()`
(pre/post index + signed synapse count), `annotations()` (indexed by
root_id) and `to_index()`. Bump `SIM_VERSION` 0.0.1 → **0.0.2**
(patch: new module, no verdict pipeline exists yet).

**Why:** One source of truth for paths and schemas; P1-5's PyTorch
model and the Brian2 validation load identical tables.

**sim-change steps 2–4:** not applicable yet — the determinism and
balance tests and the verdict pipeline arrive in P1-9 / P1-5–P1-8.
`tests/test_data.py` checks row counts and that the connectivity
`*_Index` columns match Completeness order exactly (all 15.1 M edges).

**Surprise (documented for P1-4/P1-8):** annotation `side` is the
**mirror** of the side labels in Shiu et al. 2024 (v630-era
convention). All 20 of Shiu's "right" sugar GRNs are `side == "left"`
in the v783 annotations; his "left" MN9 is `side == "right"`. Treat
annotation `side` as the source of truth and never mix in side labels
from older papers or code without checking.

**Impacts:** `sim/src/borer_sim/data.py`, `version.py`,
`sim/tests/test_data.py`.

---

## 2026-10-20 — `borer_sim.anatomy` + side convention verified (SIM_VERSION 0.0.3)

**Context:** P1-4. The turning readout and the left/right antenna input
depend on knowing what annotation `side` means, and the simulator needs
named neuron sets without hard-coded IDs.

**Decision:**
- Add `sim/src/borer_sim/anatomy.py`: `cell_type`, `orns`,
  `turning_dns` (DNa02), `giant_fiber` (DNp01), `orn_glomeruli`. Sets
  are filters on `data.annotations()`, restricted to the model, returned
  as sorted model indices via `data.to_index()`. No root_id in code.
- **Annotation `side` = the fly's own side**, and it stays the source
  of truth. Bump `SIM_VERSION` 0.0.2 → **0.0.3** (patch: new module, no
  verdict pipeline yet).

**Evidence for the side convention:**
1. FlyWire Codex FAQ: FAFB was imaged L/R inverted; FlyWire inverted
   all side labels to correct it (imagery unchanged). fafbseg docs: the
   official `side` labels "are biologically correct".
2. Soma coordinates: `left` median `soma_x` 77,736 (max 136,224,
   n=58,611); `right` median 183,856 (min 123,632, n=59,395); 0.004% of
   left somas above the global median. Low x = image left = fly's left
   per fafbseg.
3. Shiu 2024 (v630, pre-correction labels) is mirrored exactly — logged
   2026-10-19.
4. Asymmetric-body types are strongly lateralized (`SA1` 0 L / 12 R,
   `SA2` 9 L / 0 R) — suggestive only; confirming needs per-neuropil
   synapse data we haven't downloaded.

**Findings for P1-6 / P1-8 (not decided here):**
- 53 ORN glomeruli, 1,114 L / 1,132 R ORNs. None below 3 per side (min
  VA5: 6 L / 5 R). L/R ratio ≥ 1.5: **DC2** 8/12, **VC4** 9/14,
  **VM5v** 9/14. **DA2** (geosmin) 16/22 = 1.38 — a raw-count side bias
  the smell mapping must normalize if DA2 is used. **V** (CO₂) 34/33.
- Six glomeruli are fed by the **maxillary palp** (`nerve == "MxLbN"`),
  not the antenna: VA4, VA7l, VC1, VC2, VM7d, VM7v. P1-6 decides whether
  "left antenna" may use them.
- Steering-DN candidates for P1-8 (one per side each, all in model):
  DNa01, DNa03, DNa04, DNa11, DNb05, DNb06, DNg13, DNp09 (DNb02: two per
  side). DNa02 remains the spec's turning DN; nothing chosen yet.
- Giant Fiber pair has mismatched predicted NT (L acetylcholine,
  R glutamate) — a prediction artifact to keep in mind if the GF output
  sign ever matters.

**sim-change steps 2–4:** not applicable yet (no verdict pipeline);
`tests/test_anatomy.py` pins counts, model membership, filter match and
L/R disjointness. Full suite: 19 passed.

**Impacts:** `anatomy.py`, `version.py`, `tests/test_anatomy.py`,
`tests/conftest.py` (shared `needs_data` skip marker),
`.claude/skills/flywire-data/SKILL.md`.

---

## 2026-10-20 — PyTorch whole-brain LIF model (SIM_VERSION 0.1.0)

**Context:** P1-5 — the product simulator must reproduce Shiu's model
(validated via Brian2 in P1-3) within the performance budget.

**Decision:** `sim/src/borer_sim/model.py` (CPU PyTorch, float32,
0.1 ms exact linear integration, CSR delivery of spiking neurons only,
seeded Bernoulli Poisson drive, returns counts + 20 ms bins).
`borer_sim/params.py` is the single source of LIF constants for both
engines; `data.edges()` feeds both. `SIM_VERSION` 0.0.3 → **0.1.0**
(minor: the simulator now exists and produces output).

**Brian2 semantics adopted:** `(unless refractory)` is a conditional
write, so synaptic input reaching a refractory neuron is **discarded**.
Found by tracing Brian2 after the first torch version ran about 25% hot.
Shiu's published results include this behaviour, so we match it.

**Numbers (30 trials/condition vs Brian2, criteria ±10% MN9, ±15%
active):** sugar MN9 88.93 vs 89.93 Hz (−1.1%), partner 62.40 vs 62.83
(−0.7%), active 390.7 vs 395.0 (−1.1%); sugar+bitter MN9 6.73 vs 6.80
(−1.0%), partner 12.13 vs 11.70 (+3.7%), active 355.3 vs 352.1
(+0.9%); bitter active 82.9 vs 83.4; baseline and bitter MN9 exactly
0. 13/13 PASS. Exact spike-for-spike match on a deterministic 3-neuron
test.

**Performance (x86 WSL2, median of 5, loaded model):** 2 threads —
sugar 3.80 s / 8.86 s, ORN 7.27 s / 13.05 s for 1 s / 2 s simulated;
1 thread ORN 2 s = 16.33 s (over target); 4 threads no better.
Load 0.3–0.4 s, build 0.3–0.5 s, peak RSS 1.98 GB.

**sim-change steps:** determinism test added and passing
(`test_determinism.py`). The balance test is not applicable until the
verdict pipeline exists (P1-6–P1-9). Full suite: 23 passed.

**On P1-10 (subcircuit):** not needed on these numbers — every case
fits ≤ 15 s at 2 threads. But the 2 s worst case leaves only about 13%
margin, measured on x86 not the ARM server. If P1-9 or ARM
measurements exceed the budget, try cheaper fixes **before** a
subcircuit: (a) 1 s hearings, (b) skipping quiescent neurons (the
2.1 s/sim-s no-input floor is pure per-step overhead). Decision
deferred to P1-9's measurements.

**Impacts:** `model.py`, `params.py`, `data.py`, `version.py`,
`validation/{shiu_brian2,sugar_mn9,torch_vs_brian2,bench}.py`,
`tests/test_model_vs_brian2.py`, `tests/test_determinism.py`.

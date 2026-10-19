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

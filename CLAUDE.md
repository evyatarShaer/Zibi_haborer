# HaBorer (הבורר) — Claude context

A WhatsApp-shared web game: two people argue; a simulation of a real
fruit-fly brain (FlyWire connectome, ~140k neurons) picks a winner. The
fly's choice is the verdict — the humor is the point.

**Source of truth for product decisions:** [`docs/SPEC.md`](docs/SPEC.md)
**Decision log:** [`docs/DECISIONS.md`](docs/DECISIONS.md)
**Task list (per phase):** [`docs/TASKS.md`](docs/TASKS.md)

## Working rules (every session)

- **Spec-first, phase-by-phase.** Every phase has exit criteria in
  `docs/SPEC.md §12`. Don't move on until they pass.
- **Commit everything, always.** Every change — code, docs, config,
  spec edits — is committed as soon as it forms one coherent step. One
  logical step per commit, clear message. Push after every commit.
  Never end a turn with uncommitted changes (a Stop hook enforces this).
- **GitHub via MCP.** The repo is connected through the `github` MCP
  server (`.mcp.json`, token from the `GITHUB_PERSONAL_ACCESS_TOKEN` env
  var). Use it for issues, PRs and repo lookups; use plain `git` for
  commits and pushes.
- **Free services only.** Never add a paid service or a time-limited
  trial. If something needs a new external service, stop and ask.
- **No AI/LLM in the product's decision path, verdict text, or
  moderation.** The verdict is purely the simulated fly brain. Using AI
  to *write code* is fine.
- **Determinism.** Same case + same arguments + same `sim_version` =
  bit-identical result on the same platform. All randomness seeded.
- **Platform.** Workstation runs Windows, but the project **lives in
  the WSL2 (Ubuntu) filesystem at `~/projects/Zibi_haborer`**. Always
  run Claude Code, git, `uv`, and pytest from inside WSL on that path.
  Never work from `/mnt/c/...` — cross-filesystem I/O is ~25× slower
  (233 s vs 9 s for the smoke tests; see DECISIONS.md 2026-10-19). The
  `/mnt/c/Users/evyatar 2/Desktop/Zibi_haborer` copy is a stale backup
  only; do not edit it. Python 3.12 with `uv` (fallback: `venv`).
- **Parallel sim runs:** workers × torch threads ≤ 6 (physical cores)
  **and** workers × 2.5 GB ≤ available RAM (`free -g`, "available").
  WSL currently has 10 GB / 12 logical CPUs → 3 workers × 2 threads.
  Set in `sim/validation/steering_probe.py` (`WORKERS`, `THREADS`).
- **Large data files never go into git.** `sim/data/raw/` and
  `sim/data/processed/` are gitignored.
- **Stop and ask before:** downloading anything over ~1 GB; deleting
  files; changing a decision listed in the spec.
- **Code and comments in English.** User-facing product text is Hebrew
  (RTL).

## Code quality (enforced)

- **Max 200 lines per code file** (`.py`, `.ts`, `.tsx`, `.js`, `.jsx`,
  `.mjs`, `.css`, `.sql`, `.sh`). If a file would grow past 200 lines,
  split it into focused modules *before* adding more. Checked by
  `scripts/check_file_length.sh` after every Claude edit (PostToolUse
  hook) and on every `git commit` (`.githooks/pre-commit`). Docs
  (`.md`), lockfiles and data are exempt.
- **No duplicated logic.** Before writing a function, search the repo
  for one that already does the job. If two places do the same thing,
  extract one shared function and call it from both. When you touch
  code that repeats itself, consolidate it in the same commit.
- **Keep it lean.** Simplest code that meets the spec. Delete dead code
  instead of commenting it out.
- **Fresh clone:** run `git config core.hooksPath .githooks` once.

## Repo layout

```
docs/          SPEC.md, DECISIONS.md, TASKS.md, POC_REPORT.md (later)
sim/           Phase 1 lives here (Python)
  data/raw/        gitignored
  data/processed/  gitignored
  notebooks/
  src/borer_sim/
  tests/
api/           empty placeholder (Phase 2)
web/           empty placeholder (Phase 2)
scripts/       repo checks (file length, clean tree)
.githooks/     git hooks (pre-commit → file-length check)
.mcp.json      GitHub MCP server config
.claude/settings.json  hooks (file-length after edits, clean tree on stop)
.claude/skills/
  flywire-data/    SKILL.md — anything that touches the connectome
  sim-change/      SKILL.md — any change to borer_sim
  phase-gate/      SKILL.md — before declaring a phase done
```

## Skills (invoke by name when relevant)

- **flywire-data** — any code that loads or queries the connectome.
- **sim-change** — any change to `sim/src/borer_sim` (model, mapping,
  mood, readout, thresholds).
- **phase-gate** — before declaring a phase done or starting the next.

## Current status

**Phase 1 (POC) — not yet started.** Repo is scaffolded. Awaiting user
approval before any FlyWire data downloads or heavy compute.

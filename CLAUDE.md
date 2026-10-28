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
- **Run the full test suite before every commit.** `cd api && uv run
  pytest` (all api tests; add `cd sim && uv run pytest` when `sim/`
  changed), **plus `uv run pytest -m chrome` whenever `web/` changed**
  (or anything a page shows: routes, views, verdict text). Commit only
  when they pass; if a run fails because the host stalled, rerun it and
  say so in the commit. Never let a pipe (`| tail`) hide pytest's exit
  status in a commit chain.
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
  Set in `sim/validation/runner.py` (`WORKERS`, `THREADS`).
- **Long runs (> ~10 min) run detached; never poll them.** Launch with
  `scripts/detach.sh <unit> <log> <cmd...>` (a `systemd-run --user`
  service), logging a progress counter to the log. Check with
  `systemctl --user status <unit>` and `tail <log>`; stop with
  `systemctl --user stop <unit>`. Keep the screen on and the lid open
  during long runs: Windows Modern Standby slows WSL ~8× (balance run,
  DECISIONS.md 2026-10-25). **Never** use `setsid nohup ... &` or
  tmux for this: under WSL they stay in the terminal's `/init` session
  (cgroup `/non-systemd`) and die when Claude Code exits (taste_chain5,
  2026-10-22). Resumable jobs (`runner.run_jobs` skips saved keys) are
  relaunched with the same command. Give the user the check command, then
  end the turn. Reason: the Claude Code UI used ~24% CPU on Windows
  during long polls, and the PC throttled to 1.79 GHz.
- **Friends beta (P2B-12, from the laptop).** `scripts/beta.sh` starts
  the quick tunnel, then the server with `BORER_PUBLIC_URL` = the tunnel
  address, and prints it; `status` / `stop` / `restart-tunnel`. Never
  restart the tunnel during the beta: a new address breaks every link
  already sent (the script reuses a running tunnel and asks before a
  new one). No server exists yet (Oracle blocked, 2026-10-28).
- **Play-testing (Phase 2A).** Server: `scripts/detach.sh haborer
  api/data/server.log scripts/run_local.sh` (port 8000; restart with
  `systemctl --user restart haborer`). Phone: `scripts/tunnel.sh`
  (Cloudflare quick tunnel, unit `haborer-tunnel`; prints a new
  `https://*.trycloudflare.com` URL on every start; stop with
  `systemctl --user stop haborer-tunnel`). The tunnel runs with
  `--protocol http2`: **QUIC (UDP 7844) is blocked on the owner's
  network**, so QUIC quick tunnels registered a URL but answered 530.
  The script prints the URL only after the first "Registered tunnel
  connection" line, from the metrics `/quicktunnel` endpoint
  (127.0.0.1:20241); log in `api/data/tunnel.log`, tail with
  `scripts/tunnel.sh log`. **LAN access does not work:**
  phones timed out on `http://<Wi-Fi IP>:8000` even with a Hyper-V
  firewall rule for TCP 8000 (WSL mirrored mode). The rule was removed;
  don't retry it (DECISIONS.md 2026-10-25). Anyone with the tunnel URL
  can use the app while it runs.
- **Running the 2A version (one-screen page) next to 2B.** `main` has no
  `/hearing` API any more. Use a worktree at the tag, on its own port and
  its own DB (`api/data/` inside the worktree):
  `git worktree add --detach ../Zibi_haborer_2a phase-2a-done`, then
  `ln -s ~/projects/Zibi_haborer/sim/data/raw ../Zibi_haborer_2a/sim/data/raw`
  (the FlyWire files are git-ignored) and `cd ../Zibi_haborer_2a/api && uv sync`.
  Run it with `scripts/detach.sh haborer2a data/server.log env BORER_PORT=8001
  ../scripts/run_local.sh` from that `api/` dir; stop it with
  `systemctl --user stop haborer2a`. The worktree exists (made 2026-10-26).
  Never commit from it.
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
api/           Phase 2A local API (own uv project; tests: cd api && uv run pytest)
web/           Phase 2A static page (Hebrew RTL, no framework), served by the API
scripts/       repo checks (file length, clean tree); run_local.sh (2A server), tunnel.sh (phone access)
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

**Phase 1 (POC) — done, gate passed 2026-10-25** (tag `phase-1-done`, SIM_VERSION 0.8.0). **Phase 2A (Local UI POC) — done, gate passed 2026-10-25** (tag `phase-2a-done`; determinism check `python -m borer_api.recheck`; SPEC §14, TASKS P2A-1…9; P2A-1 done, `borer_sim.hearing`, SIM_VERSION 0.8.1; P2A-2 done, `borer_api.store`; P2A-3 done, `borer_api.app`, SIM_VERSION 0.8.2; P2A-4…8 done, `web/`, play-tested 2026-10-25). **Phase 2B (MVP) — in progress** (P2B-1 done: hunger 0.25 / h; P2B-4 done, SIM_VERSION 0.9.0, balance 8/8; P2B-5 done, `borer_api.cases`; P2B-6 done, case API `/api`, 2A `/hearing` API removed; P2B-7 done, word filter + report + `borer_api.admin`; P2B-8 done, case pages, Chrome page tests `cd api && uv run pytest -m chrome`; B bound on submit (2026-10-27); P2B-9 done, live meters + brain view + `/how`; P2B-10 done, preview tags + Pillow images (`borer_api.og`/`ogimage`), headlines only in `borer_api.verdicts`; P2B-11 done, share counters (`borer_api.admin counters`); P2B-2/3 blocked or deferred (no server); P2B-12 prepared, `scripts/beta.sh`; SPEC §15, TASKS P2B-1…13; Oracle Always Free ARM + Caddy + DuckDNS, same FastAPI + SQLite + static page). Details:
`docs/POC_REPORT.md`, `docs/TASKS.md`.

- **Done:** P1-1 environment, P1-2 FlyWire v783 data, P1-3 Shiu sugar→MN9
  reproduced, P1-4 flywire-data skill, P1-5 PyTorch LIF matching Brian2.
- **Done:** P1-6 taste input (0.6.0). "Taste of words" (SPEC §4; smell
  of words dropped: whole-brain cascade, no side signal). Letters → GRN
  groups (table v4) in `borer_sim.taste`; each argument tasted alone on
  both sides for **1.5 s** (2 s = fallback); verdict = higher MN9 rate;
  hearing 8.87 s. Spam fix: per-group cap 120 Hz, coverage scaling,
  no-Hebrew baseline, r_base 2 Hz; spam/silence suite + OLD+NEW + THIRD
  pass (longer-wins measured over all pairs, changed after THIRD; see
  DECISIONS.md 2026-10-22, SIM_VERSION 0.6.0).
- **P1-10 subcircuit — not needed; built, not adopted** (`borer_sim.subcircuit`):
  only N = 6 matches the full brain, with no speed-up. Parallel tastings
  (2 processes × 1 thread) are the adopted speed-up.
- **Done:** P1-7 mood (`borer_sim.mood`: hunger gain, arousal ≤ 0.45
  → noise ≤ 4.5 Hz, 0.8.0) and P1-8 readout/outcomes (`borer_sim.readout`; thresholds
  only in `params.OUTCOME`: gap 5%, froze 6 Hz, food 0.8, flips 8;
  calibrated by `validation.mood_calib`). **Fled dropped** (GF never
  fires). See DECISIONS.md 2026-10-24.
- **Done:** P1-9 balance (2026-10-25): 1,000 random pairs; all SPEC §12
  criteria pass; hearing 6.7 s median, peak RSS ~2 GB + 1.1 GB/child. See
  DECISIONS.md 2026-10-25. P1-10 closed as not needed.
- **Done:** P1-11 POC_REPORT.md complete; P1-12 phase gate passed (2026-10-25).
  Production-host timing not measured (workstation only).
- **Validation code** (`sim/validation/`): `taste_probe` / `taste_report`
  (probe + scoring), `taste_criteria` (pass rules), `taste_spam` (spam
  suite + r_base sweep), `taste_sub`, `taste_valence`, `taste_length`,
  `runner` (shared job runner + MN9 readout), `mood_probe` (noise scan),
  `mood_calib` (outcome thresholds), `balance` (P1-9 run + timing). Smell probes deleted (git
  history).
- **Known issue:** the Windows host periodically starves the WSL VM
  (tastings taking 10–60× longer for minutes at a time); per-run
  wall-clock is logged in every result record.

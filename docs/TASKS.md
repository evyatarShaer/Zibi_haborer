# Tasks

> Lightweight replacement for Jira (no Jira MCP available in this
> environment). One Epic per phase. Check off tasks as they complete.

## Epic: Phase 1 — POC

**Goal:** prove that a connectome-driven simulation can produce
deterministic, roughly-balanced verdicts from text inputs within the
performance budget.

**Exit criteria** (from `SPEC.md §12`):
- balance: 1,000 random pairs → side A wins 45–55%
- seed consistency: ≥ 90% of non-trivial pairs (mean gap ≥ 10%) keep
  their winner in ≥ 75% of seeds
- outcome mix: Win ≥ 50%; each special outcome ≤ 15%
- input quality: MN9 range continuous; |ρ| < 0.5 with length and ד/ב/ש
  count; longer argument wins 40–60% (all pairs of the set); runaway
  < 2% of tastings
- hearing ≤ 15 s (two 1.5 s tastings)
- RAM fits in 12 GB (ideally much less)

### Tasks

- [x] **P1-1 — Environment.** WSL2 + Python 3.12 + `uv`. Project in
  `sim/` with `pyproject.toml`. Deps: `torch`, `numpy`, `pandas`,
  `pyarrow`, `pytest`, `jupyter` (`brian2` only for validation).
- [x] **P1-2 — Locate data.** Find official FlyWire v783 downloads
  (FlyWire Codex) and Shiu et al. 2024's published code (likely GitHub
  `philshiu/Drosophila_brain_model` — **verify**). If downloads need a
  login, stop and tell the user which files to download and where.
  *Done 2026-10-19: 3 files downloaded + verified (sha256, schemas) —
  see `docs/DATA_SOURCES.md`.*
- [x] **P1-3 — Validate baseline.** Reproduce one known result from
  Shiu's model (e.g. sugar-sensing neurons activating feeding-related
  neurons).
  *Done 2026-10-20: sugar GRNs → MN9 reproduced on v783, 7/7 checks —
  see `docs/POC_REPORT.md`.*
- [x] **P1-4 — Fill flywire-data skill.** Replace placeholders with real
  column names, IDs, side labels, and the specific IDs for V (CO₂), DA2
  (geosmin), DNa02 family, Giant Fiber (DNp01 — verify).
  *Done 2026-10-20: skill verified, `borer_sim.anatomy` added, side =
  fly's own side — see DECISIONS.md.*
- [x] **P1-5 — Implement LIF in PyTorch.** Match Shiu's outputs on the
  same input within tolerance.
  *Done 2026-10-20: 13/13 checks vs Brian2; 2 s run 13.05 s at 2
  threads — see `docs/POC_REPORT.md`.*
- [x] **P1-6 — Implement taste.py.** Normalization, letter→GRN group
  table (v4), saturation, `!`/`?` handling, side balancing. Unit tests.
  *Done 2026-10-22 (SIM_VERSION 0.6.0). Ported 2026-10-22 ("taste of
  words" replaced "smell of words", SPEC §4; 0.5.0), then reopened the
  same day: spamming one letter defeated saturation. Fixed with a
  per-group cap (120 Hz), coverage scaling, no-Hebrew baseline and
  r_base 2 Hz: the spam/silence suite passes (no runaway, strongest spam
  דבש × 93 at 21.5 Hz < natural P75) and OLD+NEW + THIRD pass every
  criterion, with longer-wins now measured over all pairs (changed after
  seeing THIRD's 39% on 30 probe pairs; 47% on all 190) — see
  DECISIONS.md 2026-10-22.*
- [x] **P1-7 — Implement mood.py.** Hunger and arousal with their
  effects.
  *Done 2026-10-24 (SIM_VERSION 0.7.0). Hunger gain 0.5 on class-E
  groups; arousal = random-sign 2 mV noise kicks up to 10 Hz (20 Hz
  ignites runaways). On OLD+NEW mood changes 10.5% of verdicts, flips
  3.2% of winners; runaway 0.9% of tastings — DECISIONS.md 2026-10-24.*
- [x] **P1-8 — Implement readout.py.** A hearing = two tastings (one
  per argument, same seed, 1.5 s each, run in parallel). Readout = MN9
  (L + R) per tasting → `A`, `B`, `margin`, `gap`; `decision_time_ms`
  and `direction_flips` from the binned A − B; `active_neurons`;
  `deciding_neuron` (more active MN9 of the winning tasting);
  Outcomes per SPEC §7: Froze (both MN9 < 6 Hz) → Went for food
  (hunger > 0.8, gap < 5%) → Dithered (≥ 8 flips, gap < 5%) → Win
  (gap ≥ 5%) → Plain tie.
  *Done 2026-10-24 (SIM_VERSION 0.7.0). Thresholds calibrated on 600
  OLD+NEW hearings by a rule fixed before running: froze 2 → 6 Hz, flips
  3 → 8; mix Win 96.2%, dithered 3.2%, tie 0.3%, froze 0.2%, food 0.2%.
  Fled dropped: GF fired in 0/1,200 tastings — DECISIONS.md 2026-10-24.*
- [x] **P1-9 — Determinism + balance tests.** Determinism: same input
  twice → identical metrics. `test_balance.py`: balance (1,000 seeded
  random pairs, side A wins 45–55%), seed consistency (≥ 90% of
  non-trivial pairs keep their winner in ≥ 75% of seeds) and outcome
  mix (Win ≥ 50%, each special outcome ≤ 15%), exactly as in the exit
  criteria above. Measure hearing time and peak RAM. Platform recorded
  once per run in DECISIONS.md (amended 2026-10-25; result rows carry
  a `platform` field from then on, no backfill).
  *Done 2026-10-25 (SIM_VERSION 0.8.0), `tests/test_balance.py` 8/8: side
  A 46.3% (415/897); seed consistency 32/35 = 91.4%; mix win 89.7%,
  dithered 8.2%, food 1.7%, tie 0.4%, froze 0; runaway 0.38%; longer
  wins 44.7%; hearing median 6.69 s, 20/20 match the records; peak RSS
  1.98 GB + 1.14 GB per child. Platform in DECISIONS.md 2026-10-25.*
- [x] **P1-10 — Subcircuit (if needed).** Only if full-brain runs blow
  the budget. Compare against full-brain results.
  *Not needed 2026-10-25: N = 6 matched the full brain but gave no
  speed-up, and full-brain hearings take 6.7 s (budget 15 s).
  `borer_sim.subcircuit` is kept but not adopted.*
- [x] **P1-11 — docs/POC_REPORT.md.** All numbers + decisions made during
  POC. *Done 2026-10-25: P1-9, P1-10, timing scope and summary sections;
  input quality re-measured at 0.8.0 on the balance data (band 24.3%,
  ρ length −0.07, ρ ד/ב/ש +0.01).*
- [x] **P1-12 — Run `phase-gate` skill.** Confirm every exit criterion.
  *Passed 2026-10-25, tag `phase-1-done` (DECISIONS.md 2026-10-25 —
  Phase 1 gate passed).*

## Epic: Phase 2A — Local UI POC

**Goal** (SPEC §12, §14): try the whole experience on the workstation:
input, waiting, verdict for every outcome, appeal, brain view, 7-day
retention. FastAPI + one static HTML page (Hebrew, RTL, no framework) +
SQLite, written so it can move to a server unchanged.

**Exit criteria** (from `SPEC.md §12`):
- The whole flow works end to end in a mobile-width browser (RTL):
  input → waiting → verdict → appeal → brain view, for every outcome.
- Determinism: every stored hearing reruns bit-identically from its seed
  (same platform).
- Submit → verdict ≤ 15 s on the workstation; the waiting screen never
  looks stuck.
- No API response or page exposes the letter → GRN table (automated).
- The cleanup deletes hearings older than 7 days (test).

**Layout:** `api/` (FastAPI app, imports `borer_sim`), `web/` (static
page, split into files ≤ 200 lines). Config (DB path, host, port) comes
from env, with no workstation paths in code.

### Tasks (build order)

- [x] **P2A-1 — Product hearing in `borer_sim`.** Add one function:
  (text A, text B, seed) → metrics, outcome, mood and the brain summary.
  - The mood draw moves from `validation.mood_calib.product_mood` into
    `borer_sim.mood` (simulated wait, DECISIONS.md 2026-10-25), and
    validation imports it from there.
  - Parallel tastings (2 processes × 1 thread) move from
    `validation.runner.timed_hearings` into `borer_sim`, shared by both.
  - Brain summary: MN9 rate per 50 ms bin per tasting, activation per
    taste group (no letters), mood, seed, `SIM_VERSION`, platform.
  - Run the `sim-change` skill.
  *Accept:*
  - Output for a seed doesn't change (patch bump 0.8.1, sim-change
    skill): the 20 timing hearings of `validation.balance` reproduce
    the records exactly (`test_balance` stays green).
  - The same seed twice gives a bit-identical result and summary
    (test).
  - The summary has no per-letter field (test).
  *Done 2026-10-25 (SIM_VERSION 0.8.1):*
  - `balance time` 20/20 match the records (median 7.23 s);
    `hearing.run` 10/10 match (median 7.35 s, max 9.27 s).
  - Same seed twice gives a bit-identical result; a different seed
    differs.
  - The brain summary is per taste class (15 classes), with no letters
    and no GRN-group names (`tests/test_hearing.py`).
  - Full suite: 97 passed. DECISIONS.md 2026-10-25 (P2A-1).
- [x] **P2A-2 — SQLite storage + 7-day cleanup.** `hearing` table: id,
  created_at, topic, name_a, name_b, text_a, text_b, seed, hunger,
  arousal, status (running / decided / failed), metrics (JSON), outcome,
  winner, brain (JSON), sim_version, platform, duration_ms, appeal_of
  (FK; the appeal row is deleted with the original). The cleanup deletes
  rows older than 7 days; it runs at startup and on a timer.
  *Accept:*
  - Tests on a temp DB: insert, read, appeal link; the cleanup removes
    exactly the rows older than 7 days (injected clock).
  - The schema is created on first run.
  *Done 2026-10-25:* `api/src/borer_api/store.py`, `api/tests/test_store.py`
  (13 passed).
  - The ids are unguessable (`token_urlsafe(9)`).
  - One appeal per original, enforced in the DB (`appeal_of` UNIQUE + FK
    ON DELETE CASCADE): a younger appeal goes when its original
    expires.
  - Rows past 7 days read as gone even before the purge.
  - `fail_running()` marks hearings orphaned by a restart.
  - `cleanup_loop` purges at start and then on a timer. It is wired
    into the app's startup in P2A-3.
- [x] **P2A-3 — FastAPI API.** The model loads once at startup.
  - `POST /hearing` (topic?, names, arguments) checks the argument rules
    (≥ 10 Hebrew letters, ≤ 280 chars, names required), draws a random
    seed, starts the hearing in the background and returns `id`.
  - `GET /hearing/{id}` returns status, then the verdict data: outcome,
    winner name, A/B for the meter, mood, topic, `appeal_of`,
    `can_appeal`.
  - `GET /hearing/{id}/brain` returns the stored summary.
  - `POST /hearing/{id}/appeal` (P2A-7).
  - The app serves `web/`.
  *Accept:*
  - API tests with a fake sim: validation errors in Hebrew, 404 for
    unknown or deleted ids, status running → decided.
  - An allowlist test asserts that no response contains letter-level or
    table data.
  - One real end-to-end hearing finishes in ≤ 15 s (POST → decided)
    on the workstation.
  *Done 2026-10-25 (SIM_VERSION 0.8.2):* `api/tests/test_app.py` +
  `test_store.py` 33 passed (30 runs in a row); `test_live.py` passed with
  `-W error::DeprecationWarning`.
  - Startup 3.2 s. Submit → decided 6.74 / 8.13 / 7.43 s.
  - The stored result equals a fresh rerun from its seed.
  - Process tree RSS 3.82 GB.
  - Model and pool load once, in the lifespan ("forkserver" workers,
    no fork warning).
  - One hearing runs at a time, with up to 3 waiting (status
    `queued`). More → 503 with "הזבוב עסוק…".
  - The purge loop is started in the lifespan.
  - Binds 0.0.0.0:8000, started with `scripts/run_local.sh`.
- [x] **P2A-4 — Input screen.** Hebrew RTL, mobile-first, no framework:
  topic (optional, labelled as not tasted), two sides with name and
  argument. A live 10-letter counter uses the same normalization as §4.1
  (one shared JS helper, tested against `borer_sim.taste` on the
  spam/silence texts).
  *Accept:*
  - Submit stays disabled until both arguments are valid.
  - The server rejects the same cases.
  - Usable at 360 px width.
  *Done 2026-10-25: built in `web/` (`api/tests/test_web.py`); the owner
  play-tested it on a phone through the tunnel. The placeholder Hebrew
  copy stays until the owner rewrites it.*
- [x] **P2A-5 — Waiting screen.** Mood story line → "tasting side A" →
  "tasting side B" → "deliberating", which loops. Polls
  `GET /hearing/{id}`.
  *Accept:*
  - Something animates at all times.
  - A slow host (sim delayed to 40 s, fake) still loops cleanly.
  - A failed hearing shows a Hebrew error with a retry.
  - Shown on screen: about 7 s at the measured speed.
  *Done 2026-10-25: built in `web/` (`api/tests/test_web.py`); the owner
  play-tested it on a phone through the tunnel. The placeholder Hebrew
  copy stays until the owner rewrites it.*
- [x] **P2A-6 — Verdict screen.** Courtroom front with a placeholder
  judge fly (emoji/SVG). Topic line "התיק: {topic}" above the headline
  (hidden when there is no topic); headline per outcome (SPEC §7);
  appetite meter per side; "what happened in the brain?" button; appeal
  button (original hearings only).
  *Accept:* each of the 5 outcomes renders correctly from fixture data
  (Win, Dithered with a name, Tie, Froze, Lunch break). With a topic,
  the line "התיק: {topic}" appears above the headline; without one, the
  line is absent (not an empty line).
  *Done 2026-10-25: built in `web/` (`api/tests/test_web.py`); the owner
  play-tested it on a phone through the tunnel. The placeholder Hebrew
  copy stays until the owner rewrites it.*
- [x] **P2A-7 — Appeal.** `POST /hearing/{id}/appeal`: one per hearing;
  same texts and names, new random seed, stored with `appeal_of`. The
  result screen shows "הערעור התקבל!" if the winner changed, otherwise
  "הערעור נדחה. הפסק סופי". The appeal hearing shows no appeal button.
  *Accept:*
  - API tests: a second appeal is refused (409); appealing an appeal is
    refused.
  - The comparison uses the outcome winner (a non-win outcome counts as
    "no winner").
  *Done 2026-10-25: built, then play-tested by the owner on a phone through the tunnel:*
  - API: `app.py` `POST /hearing/{id}/appeal` (201 / 404 / 409 for an
    undecided hearing, a second appeal or an appeal of an appeal / 503
    when the court is full, retryable). `GET /hearing/{id}` adds
    `appeal_id` and, on a decided appeal, `appeal_accepted`.
  - Page: the appeal plays the waiting story again ("ערעור! השופט חוזר
    לאולם" + the new mood), then the result line above the headline. The
    original links to its appeal.
  - Tests: `api/tests/test_appeal.py`, `test_web_lab.py`.
- [x] **P2A-8 — Brain view.** The lab view is fetched on demand:
  - MN9 rate over time, both tastings on one chart;
  - group-level taste activation bars;
  - mood, seed, SIM_VERSION, platform;
  - the line "140K neurons of a real fly brain, no AI".
  *Accept:*
  - Renders from stored data only, with no sim call (test: the sim is
    not touched on GET).
  - No letter appears in the view.
  *Done 2026-10-25: built, then play-tested by the owner on a phone through the tunnel:*
  - `web/js/lab.js` (pure model) + `brain.js` (view): fetched on the
    first tap only, then toggles.
  - MN9 chart: inline SVG, side B dashed as well as colored, with a
    display-only 250 ms moving average (raw 50 ms bins are 0/20/40 Hz
    spikes). Tap or drag for the values at a time.
  - Taste bars per class, both sides; classes under 0.5 Hz on both
    sides are hidden. Hebrew labels cover all 15 classes (test against
    `taste.classes()`).
  - Mood, seed, SIM_VERSION, platform; the "no AI" line.
  - Tests: GET brain never calls the sim; the view has no GRN-group names.
- [ ] **P2A-9 — Phase 2A gate.** Walk through every exit criterion,
  including a determinism rerun of all stored hearings, then run the
  `phase-gate` skill.

## Epic: Phase 2B — MVP (shareable / server)

**Goal** (SPEC §12): what 2A does not deliver:
- the two-device flow with a link and response window (§3, §8: tokens,
  deadline, plain water, reminder);
- hosting;
- verdict card page + OG image + WhatsApp preview (§9);
- the 10–15 s brain animation and replay;
- sudden death;
- a group-level how-it-works page;
- moderation;
- appeal-bypass prevention;
- production-host timing;
- the stack decision (§11).

**Exit criteria:** 20 real cases in friends' groups, ≥ half shared
onward.

**Carried over from Phase 1** (POC_REPORT.md summary): production-host
timing; "Brain overload" outcome decision; real-utterance arguments;
watch side-A (46.3%) and shorter-wins (44.7%) drift; FlyWire licence
(non-commercial).

**Must revisit before anything is public:** the brain view's
taste-class output still leaks a coarse letter → class map. An argument
that repeats one letter lights up that letter's class (DECISIONS.md
2026-10-25, class-level leak).

Not yet planned (after the 2A gate).

## Epic: Phase 3

Not yet planned.

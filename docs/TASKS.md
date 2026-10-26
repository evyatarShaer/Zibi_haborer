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
- [x] **P2A-9 — Phase 2A gate.** Walk through every exit criterion,
  including a determinism rerun of all stored hearings, then run the
  `phase-gate` skill.
  *Passed 2026-10-25, tag `phase-2a-done` (POC_REPORT.md Phase 2A,
  DECISIONS.md 2026-10-25 — Phase 2A gate passed):*
  - `borer_api.recheck`: 6/6 stored hearings bit-identical.
  - sim 98 passed, api 59 passed.
  - Every outcome through the full flow in headless Chrome at 360 px.
  - Submit → decided max 14.46 s on battery.

## Epic: Phase 2B — MVP (shareable / server)

**Goal** (SPEC §12, §15): a real two-device game, shared over WhatsApp,
running on a free server.
- Blind arguments with personal links, a 3 h deadline, a nudge after 1 h
  and plain water at the deadline.
- Hunger from the real wait.
- Live reveal for B and replay for A.
- Appeals: once per side, up to 3 hearings per case.
- Public card + teaser + OG images.
- Meters that fill from the MN9 curves.
- The brain view without taste classes, and a how-it-works page.
- Moderation and 7-day retention.
- Oracle Always Free + Caddy + a free subdomain.

**Exit criteria** (from `SPEC.md §12`):
- 20 real cases in friends' groups; of the decided cases, ≥ half had
  "send the verdict" tapped (server-side counter).
- On the production host: hearing ≤ 15 s (submit → verdict) and
  bit-identical determinism.

**Decided 2026-10-25:** DECISIONS.md, the eleven 2B planning entries.
**Open:** the lunch-break growth rate (P2B-1; the owner picks). The
other open items were resolved on 2026-10-26 (DECISIONS.md).

**Carried over:** real-utterance arguments; watch the side-A (46.3%)
and shorter-wins (44.7%) drift; FlyWire licence (non-commercial). Also
the owner's Hebrew copy and fly art.

### Tasks (build order)

- [ ] **P2B-1 — Lunch-break growth rate (analysis only).** From the
  saved P1-9 records (`balance_1500ms.jsonl`), with no new long run, find
  the hunger growth rate per hour. Keep the U(0, 0.4) start and the 0.8
  threshold.
  - Realistic wait patterns: B answers within minutes; ~Exp(30 min);
    ~Exp(1 h); uniform 0–3 h. Each pattern also has a no-show share
    (full 3 h).
  - Target: the lunch break in ~1–3% of all cases, mainly near the
    deadline and in no-shows.
  *Accept:*
  - A table of candidate rates: lunch-break rate per pattern; the share
    of lunch breaks with wait ≥ 2 h or a no-show; the earliest wait at
    which one is possible; the effect on win / dithered / tie / froze.
  - The method's limits stated: hunger also changes MN9, and the records
    cover hunger only up to the range P1-9 drew.
  - A POC_REPORT section. The owner picks the rate; DECISIONS entry;
    used in P2B-4.
  *Options reported 2026-10-26 (POC_REPORT.md P2B-1), awaiting the owner's
  pick:* 0.20 / 0.25 / 0.30 per hour. No-shows never give a lunch break
  (water MN9 ≈ 0 Hz).
- [ ] **P2B-2 — Host setup.** The owner creates the Oracle Cloud
  account; the signup asks for a card, and only Always Free resources
  are used. Then:
  - an ARM (Ampere A1) VM with Ubuntu, `uv` and the FlyWire v783 files
    (137 MB);
  - a free DuckDNS subdomain;
  - Caddy with automatic HTTPS;
  - the app as a systemd service, restarted on boot;
  - a deploy script from git;
  - the same env config as 2A (no workstation paths).
  *Accept:*
  - `https://<sub>.duckdns.org` serves the app after a reboot.
  - The certificate renews automatically (Caddy).
  - No paid resource exists in the tenancy (checked in the console).
  - Risk noted: Oracle may reclaim idle Always Free VMs; check the
    current rule and keep a note in DECISIONS.
- [ ] **P2B-3 — Production-host timing and ARM determinism.** 20
  timing hearings on the server.
  Run with the 2A app and sim right after setup; it decides whether the
  host works at all. Re-measured on the 2B sim at the gate.
  *Accept:*
  - Submit → verdict ≤ 15 s (median and max reported).
  - Peak RAM measured.
  - Same seed twice bit-identical on ARM.
  - `borer_api.recheck` reports 100% on the server DB.
  - The agreement of ARM verdicts with the x86 records (balance timing
    set) is reported (not required to be equal: §2.2 is per platform).
  - If > 15 s: stop and decide (fallback: worker on the home PC).
- [ ] **P2B-4 — `borer_sim` for 2B** (`sim-change` skill; version bump).
  - The product hearing takes the real wait: `mood.from_case(seed,
    wait_h)`. The 2A simulated wait stays only for 2A tests and
    validation.
  - Plain water as side B: baseline GRN rates only (the no-Hebrew
    baseline).
  - The brain summary drops `taste_hz`.
  - The hunger growth rate picked in P2B-1. An appeal's hunger is the
    case's own wait with a fresh U(0, 0.4) start from the appeal's seed.
  *Accept:*
  - Same seed + wait twice gives bit-identical results (test).
  - The water hearing runs ≤ 15 s and is deterministic (test).
  - The summary has no taste-class field (test).
  - The balance check per the skill; full sim suite green.
- [ ] **P2B-5 — Case storage.** SQLite schema per SPEC §10:
  - `case`, `hearing` (n 0–2, `appealed_by`), `report` and `counter`;
  - token hashes;
  - a purge 7 days after case open (counters kept);
  - `hidden_at` and `shared_at`.
  The 2A `hearing` table is retired (2A data is not migrated).
  *Accept:*
  - Tests on a temp DB: create → B submits → decided; at most 3 hearings
    per case and one appeal per side, enforced in the DB; the purge
    removes exactly the cases older than 7 days, with their children;
    counters survive the purge (injected clock).
- [ ] **P2B-6 — Case API.**
  - A opens a case and gets their link. B submits through B's link.
  - A deadline sweep in the process runs the plain-water hearing at 3 h.
  - The nudge becomes available at 1 h.
  - Appeals: per side, within 3 h of the latest verdict, on the original
    arguments with a fresh seed; the latest verdict is final.
  - The one-courtroom queue as in 2A.
  - Expired, deleted or hidden cases → one generic "case closed" answer.
  *Accept:*
  - API tests with a fake sim:
    - B's token never receives `text_a` while waiting;
    - a wrong token gets 404 (no difference between "wrong" and "gone");
    - the deadline fires the water hearing (fake clock);
    - the nudge is hidden before 1 h;
    - a second appeal by the same side, a 4th hearing and an appeal
      after 3 h are refused;
    - "accepted" uses the previous verdict's winner.
  - The allowlist test from 2A extended (no letter or table data, no
    arguments on public endpoints).
  - Only A may appeal a no-show.
  - The first device to open B's link (via a page API call, never the
    HTML GET) is bound as B. Others get "התיק כבר בטיפול". A's device is
    never bound as B. Tested: a crawler-style GET does not claim B.
  - 20 new cases per day per IP (hashed); the 21st is refused (test).
- [ ] **P2B-7 — Moderation.**
  - A Hebrew offensive-word filter on the topic, names and arguments,
    after §4.1 normalization. The owner supplies the list. A match gives
    a soft block with a fly-themed message.
  - A report button that hides the case at once.
  - An admin command: `python -m borer_api.admin list|delete|restore`.
  *Accept:*
  - Tests: listed words are blocked after normalization (final letters,
    niqqud); clean text passes.
  - A report hides the whole case immediately: the public card and both
    personal pages show "case closed".
  - Delete and restore work. No AI anywhere.
- [ ] **P2B-8 — Pages: case flow.** Hebrew RTL, mobile-first, the 2A
  modules reused:
  - A's open-case screen + "send to the other side" (`wa.me`);
  - A's waiting page with a "nudge again" button from 1 h;
  - B's blind input;
  - B's live story → verdict → "send the verdict";
  - A's replay from stored data;
  - the history line; the appeal button with its window;
  - the "this link is personal" note;
  - the generic "case closed" page.
  *Accept:*
  - Node tests for each screen model.
  - The full two-link flow in headless Chrome at 360 px, for every
    outcome, a no-show and an appeal chain of 3 (scripted sim, as at
    the 2A gate).
  - No horizontal overflow.
- [ ] **P2B-9 — Live meters, brain view, how it works.**
  - The appetite meters fill from the stored MN9 bins during the story
    (cumulative rate), live and on replay; hidden on Froze.
  - The brain view without taste bars (MN9 curves, mood, seed,
    `SIM_VERSION`, platform), on personal pages only.
  - The no-show headlines: "הזבוב העדיף מים" when water wins, otherwise
    "הצד השני לא התייצב לדיון".
  - A general how-it-works page with the credits in SPEC §15.7 (FlyWire
    citation table, checked 2026-10-26; Shiu et al. 2024).
  *Accept:*
  - The meter's end value equals the stored A/B share (test).
  - Froze shows no meters.
  - The lab view and the how-it-works page contain no letter, GRN group
    or class table (automated check).
- [ ] **P2B-10 — Public card, teaser and OG images.**
  - Server-rendered OG tags for the teaser (B's link: fly + topic, no
    verdict) and the public card (topic, names, final verdict, history,
    no arguments).
  - 1200×630 images drawn with Pillow, with RTL Hebrew shaping
    (libraqm).
  *Accept:*
  - Tests: no argument text in the public page or any image's source
    data; the teaser has no verdict.
  - Hebrew renders right to left with joined final forms (golden image).
  - A real WhatsApp preview checked on the owner's phone.
- [ ] **P2B-11 — Share counters.** Server-side aggregate counters
  (`cases_opened`, `cases_decided`, `cases_shared`, no-shows, appeals,
  reports) per day, kept past the 7-day purge. An admin command prints
  them.
  *Accept:* tests: one `case_shared` per case however many taps; no case
  data in the counter table.
- [ ] **P2B-12 — Friends beta.** Run real cases in friends' WhatsApp
  groups. Fix what breaks.
  *Accept:* 20 decided real cases; counters show the shared share.
- [ ] **P2B-13 — Phase 2B gate.** Every exit criterion with evidence
  (`phase-gate` skill).

## Epic: Phase 3

Not yet planned.

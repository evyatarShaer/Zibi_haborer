# HaBorer (הבורר) — Spec

> Source of truth for product decisions. Change decisions here via a PR with
> an entry in `DECISIONS.md`.

## 1. Product

A WhatsApp-shared web game. Two people argue; a simulation of a real fruit-fly
brain (FlyWire connectome, ~140k neurons) decides who wins. Each side writes
their argument from their own phone. Arguments become *tastes* fed to the
fly's gustatory receptors; the fly tastes each argument, and the one it
wants to eat more wins.

It's a fly, not a judge — the humor is part of the product.

**Goal:** fun first. Revenue is a bonus.

## 2. Principles

1. **The fly decides.** No AI/LLM in the decision path, verdict text, or
   moderation. (Using AI to *write code* is fine.)
2. **Deterministic.** Same case + same arguments + same `sim_version` →
   bit-identical result **on the same platform** (CPU architecture +
   torch version). All randomness is seeded. Each run is computed once
   and stored; the verdict card always reads the stored result. Hearings
   are kept **7 days**, then deleted (§14).
3. **Transparent.** The verdict card shows what the brain did. There's a
   public "how it works" page. Everything shown is **group-level only**:
   the letter → GRN table is never published (not in the UI, a "how it
   works" page or an API response; DECISIONS.md 2026-10-25).
4. **Fair.** Arguments hidden until both are submitted. Each argument is
   tasted separately, on both sides of the mouth, with the same seed
   (case seed + round), so swapping the sides swaps the result exactly.
5. **Humor without humiliation.** Mock the dispute, not the loser.
6. **WhatsApp-first.** Mobile, link-based, no sign-up, good link preview.

## 3. User flow

1. **Open a case.** Side A enters: topic, own name, other side's name,
   response window (1h / 6h / 24h, default 6h), own argument. Gets a link.
2. **Share.** Side A shares the link in WhatsApp. Side B opens it, claims
   side B, writes their argument. A device that submitted one side cannot
   submit the other.
3. **Hearing.** When both have submitted (or the deadline passed), the
   "hearing" runs. Anyone with the link watches a 10–15s brain animation,
   then the verdict.
4. **Tie → sudden death (optional).** Each side adds ONE word, rerun with
   the same fly mood. Max 2 rounds. Then the tie is final.

**Argument rule:** an argument needs **at least 10 Hebrew letters** (after
§4.1 normalization) to be submitted — a deterministic check in the UI,
no AI. The simulation still handles any text safely (§4.6).

## 4. "Taste of words" (argument → receptor input)

Replaced "smell of words" on 2026-10-22 (DECISIONS.md): olfactory input
ignites a whole-brain runaway with a fixed, side-blind output.

1. **Normalize.** Strip niqqud and duplicate spaces; final letters → regular
   (ך→כ, ם→מ, ן→נ, ף→פ, ץ→צ). Count only the 22 Hebrew letters plus `!` and
   `?`. Everything else counts only toward length. **Max 280 chars.**
2. **Map.** Each Hebrew letter maps to one fixed gustatory receptor neuron
   (GRN) group: v783, one group per sub-class × cell type with ≥ 2 GRNs
   per side. Groups that ignite the runaway alone are excluded (LB3b,
   LgAG3). A group's class (excite / inhibit / neutral) is **measured in
   the simulated brain** (its effect on MN9 on a sugar background); the
   literature valence is a cross-check only. Rule (table v4): the two
   groups that drive MN9 alone (LB3c, LB3d) are split in halves and go
   to the four most frequent letters (י ו ה א), so the main drive is
   nearly constant and the other letters decide; ד/ב/ש go to the next
   exciters (PhG1c, PhG4, LB4a — the honey easter egg, moderate); the
   other 15 letters are dealt excite / inhibit / neutral by
   conversational frequency, stronger effect to more frequent letters.
   The table is fixed in code (`borer_sim/taste.py`) and is
   **confidential**: it is never published (§2.3).
3. **Intensity.** Each letter's input is its share **relative to its
   conversational Hebrew frequency** (OpenSubtitles 2018). The letters'
   total drive is fixed (scaled only by the length gain), so the text
   sets the split, not the amount.
4. **Punctuation.**
   - `!` → bitter GRNs (**LB1a**, inhibitory).
   - `?` → putative-aversive GRNs (**LB2c**, inhibitory).
   - Both capped.
5. **Length.** Logarithmic gain on overall intensity. Too much can turn
   aversive (a long text with Hebrew letters adds `!` drive). A text with
   no Hebrew letters gets the baseline rate only.
6. **Adaptation / saturation (per receptor):**
   `r = r_base + r_max * f / (f + K)` on each letter's relative share, then
   the fixed total is split, then:
   - **cap:** no group's rate exceeds **120 Hz** per GRN (natural-text
     p90; within the 10–200 Hz range Shiu et al. drive GRNs at);
   - **coverage:** each letter's excess drive × `min(1, C / 0.6)²`, where
     `C = Σ min(letter share, conversational frequency)` (how much of
     normal Hebrew letter use the text covers; natural texts ≥ 0.6).
   Spamming one letter, one word or two alternating letters therefore
   loses drive instead of gaining it. Values and evidence: DECISIONS.md.
7. **Sides.** Each argument drives the left and right GRNs of every
   group equally (same total drive per side).

## 5. Fly mood (modeled layer on top of the connectome)

> We say this publicly: it's an *added* layer, not from the connectome.

- `hunger` ∈ [0, 1] — seeded from case id; rises while waiting
  (**+0.1 / hour** from case open until both submitted, capped at 1).
  Shown in UI ("the fly has been hungry for 3 hours").
  Intentional: after ~8 h of waiting hunger exceeds 0.8, so a close case
  becomes "went for food" — a late side starves the fly.
- `arousal` ∈ [0, 0.45] — seeded from case id (uniform; capped at 0.45
  because runaways appeared only from 0.48, DECISIONS.md 2026-10-24).
  Sets background noise →
  more dither (and the odd changed verdict).

**Effects:**
- Hunger raises gain of the MN9-exciting GRN groups (drive above
  baseline × (1 + 0.5 · hunger)).
- Arousal increases background spike noise (random-sign 2 mV kicks to
  every neuron at arousal × 10 Hz, so ≤ 4.5 Hz; 20 Hz ignites runaways).
- **Hearing without a waiting time** (Phase 2A, both sides typed at
  once): the wait is drawn from the hearing seed, ≈ Exp(2 h), and
  hunger follows the rule above. This is the distribution P1-9
  validated ("went for food" ≈ 1.7%). The user never chooses the mood.
- Same seed and same mood for both tastings of a hearing. Measured on
  OLD+NEW (600 hearings): mood changes the verdict in 10.5% of hearings,
  flips the winner in 3.2% of decided ones (DECISIONS.md 2026-10-24).

## 6. Simulation & readout

- **Model.** Whole-brain leaky integrate-and-fire (LIF), following
  Shiu et al. 2024 (*Nature*). Weights from FlyWire synapse counts, sign
  from predicted neurotransmitter.
- **Data version.** FlyWire **v783**.
- **Input.** Seeded Poisson spikes in GRNs at computed rates.
- **Hearing = two tastings.** Each argument is tasted alone (one run
  each), with the same seed. **1.5 s** simulated per tasting (decided
  2026-10-22; 2 s is the documented fallback — see DECISIONS.md). The
  two tastings run in parallel.
- **Readout.** MN9 (cell type CB0701, proboscis motor neuron), left +
  right, per tasting. 50 ms bins.
- **Metrics (per hearing):**
  - `A`, `B` — total MN9 rate (Hz, L + R) of each side's tasting
  - `margin = max(A, B) / (A + B)` — winner's share, in [0.5, 1]
  - `gap = |A − B| / (A + B) = 2·margin − 1` (gap ≥ 5% ⇔ ≥ 52.5/47.5)
  - `decision_time_ms` — when the cumulative binned A − B crosses
    threshold and stays
  - `direction_flips` — number of sign flips in the binned A − B
  - `active_neurons` — count of neurons that spiked (per tasting)
  - `deciding_neuron` — the more active MN9 of the winning tasting + its
    FlyWire id
- **Replay.** Per-region activity in 20 ms frames, saved for animation.
- **Performance target.** ≤ **15 s per hearing** (both tastings).
  Measured 8.87 s on the workstation (2 processes × 1 thread). The
  subcircuit (P1-10) gives no speed-up and is not used.

## 7. Outcomes

First matching row wins. `gap` as defined in §6. Thresholds calibrated
in POC (SIM_VERSION 0.7.0, DECISIONS.md 2026-10-24); the only copy in
code is `borer_sim.params.OUTCOME`. **Fled was dropped** (2026-10-24):
the Giant Fiber never fires in a taste-driven hearing (0 of 1,200
tastings with product mood; only in a noise-saturated, runaway brain).

| Outcome        | Condition                                   | Verdict headline (HE)                         |
|---              |---                                           |---                                             |
| Froze          | both tastings' MN9 (`A`, `B`) < 6 Hz         | הזבוב קפא. התיק הזה גדול עליו                 |
| Lunch break (code `food`) | `hunger > 0.8` and `gap < 5%`     | הבורר יצא להפסקת צהריים. הדיון נדחה           |
| Dithered       | `direction_flips ≥ 8` and `gap < 5%`         | אחרי התלבטות קשה... הצדק עם {name}            |
| Win            | `gap ≥ 5%`                                   | פסק הדין: הצדק עם {name}                      |
| Plain tie      | otherwise                                    | תיקו. הזבוב לא השתכנע מאף אחד                 |

Headlines decided 2026-10-25 (DECISIONS.md). "Went for food" is renamed
to **lunch break** in all user-facing text; the code key stays `food`.
Dithered names the side with the higher MN9 rate (`winner`), even though
the gap is < 5%. The topic, if given, appears in the headline. A Win
also shows an appetite meter per side (A vs B MN9 rate).

Track outcome frequencies globally; show rarity on the card.

## 8. Side B doesn't answer

- **Reminder button.** `wa.me` link with prefilled message.
- **Deadline passes.** Side B gets "plain water" (baseline GRN rates
  only); simulation runs normally. Outcome described as "lost to silence".
- **Public defender** — Phase 3, not MVP. Anyone with the link can write
  for B after half the window elapses.

## 9. Verdict card

Page + 1200×630 OG image.

**Shows:** topic, names, winner or tie type, margin + A/B bar, decision
time, direction flips, fly mood, mini brain map, deciding neuron id, one
template sentence, rarity, buttons (share / new case / sudden death).

**Arguments appear on the page but NOT in the OG image.**

**Template sentences:** 3–5 per outcome type, human-written. Choice seeded
by case.

## 10. Data model

- **Case:** `id`, `slug`, `topic`, `side_a_name`, `side_b_name`,
  `deadline_at`, `status` (`open`|`ready`|`running`|`decided`|`expired`),
  `seed`, `hunger`, `arousal`, `created_at`.
- **Argument:** `id`, `case_id`, `side`, `round` (0 main, 1–2 sudden
  death), `text`, `author_token_hash`, `is_public_defender`,
  `defender_name`, `created_at`.
- **Run:** `id`, `case_id`, `round`, `input_rates` (jsonb, both
  tastings), `metrics` (jsonb), `outcome`, `replay_url`, `sim_version`,
  `platform`, `duration_ms`.
- **Template:** `id`, `outcome_type`, `text`, `weight`.
- **Report:** `id`, `case_id`, `reason`, `created_at`.

**No user accounts.** Each side is identified by a token cookie.

## 11. Tech stack (FREE only)

Supersedes any earlier version of the spec. **Under review for Phase
2B** (DECISIONS.md 2026-10-25). Phase 2A runs on the workstation only,
with FastAPI wrapping `borer_sim`, one static HTML page (Hebrew, RTL, no
framework) and local SQLite. 2A is written so that the same code can move
to a server unchanged. Whether 2B keeps that stack or moves to the table
below is decided in 2B planning.

| Layer          | Choice                                                                             |
|---              |---                                                                                  |
| Simulation     | Python 3.12 + PyTorch sparse (validate against Shiu's Brian2 model first)          |
| Data           | FlyWire v783 as Parquet, loaded in memory                                          |
| API            | FastAPI                                                                            |
| Queue          | **Postgres itself** (jobs table, `SELECT … FOR UPDATE SKIP LOCKED`) — no Redis     |
| DB             | Neon Postgres (free tier)                                                          |
| Frontend       | Next.js + React + Tailwind (SSR OG tags required — WhatsApp's crawler is JS-less)  |
| OG images      | `@vercel/og` (Satori)                                                              |
| Animation      | Canvas 2D (PixiJS if needed)                                                       |
| Live status    | SSE or 3 s polling                                                                 |
| Files          | Cloudflare R2 (free tier)                                                          |
| Hosting (web)  | Vercel Hobby — non-commercial only; upgrade if it ever earns money                 |
| Hosting (api)  | Oracle Cloud Always Free ARM (2 OCPU / 12 GB); beta fallback: worker on home PC    |
| Moderation     | Hebrew blocked-word list + 20 cases/day per IP + report button                     |
| Analytics      | PostHog free tier                                                                  |

## 12. Phases

1. **POC (now)** — Python only.
   **Exit:**
   - **Balance:** over 1,000 seeded random argument pairs, side A wins
     45–55%.
   - **Seed consistency** (replaces the swap test: swapping sides swaps
     the tastings exactly): ≥ 90% of non-trivial pairs (mean gap ≥ 10%)
     keep their winner in ≥ 75% of seeds.
   - **Outcome mix:** ≥ 50% of hearings end in Win; each special
     outcome (Froze / Went for food / Dithered) ≤ 15%.
   - **Input quality:** MN9 range continuous (≤ 50% of tastings in any
     band 10% of the range wide); |Spearman ρ| < 0.5 between
     per-argument MN9 and length, and the ד/ב/ש count; the longer
     argument wins 40–60% of decided hearings, measured over **all
     pairs** of the argument set (DECISIONS.md 2026-10-22, 0.6.0);
     runaway (> 4,000 active neurons) in < 2% of tastings.
   - hearing ≤ 15 s
   - RAM fits in 12 GB (ideally much less).
2. **Phase 2A — Local UI POC** (workstation only, §14) — input,
   waiting, verdict (all outcomes), appeal, "what happened in the
   brain?", 7-day retention.
   **Exit:**
   - The whole flow works end to end in a mobile-width browser (RTL):
     input → waiting → verdict → appeal → brain view, for every outcome.
   - Determinism: every stored hearing, rerun from its stored seed and
     texts, gives bit-identical metrics and outcome (same platform).
   - Submit → verdict ≤ 15 s on the workstation; the waiting screen never
     looks stuck.
   - No API response or page exposes the letter → GRN table (automated
     check).
   - The cleanup deletes hearings older than 7 days (test).
3. **Phase 2B — MVP (shareable / server)** — what 2A does not deliver:
   two-device flow with a link and response window (§3, §8: tokens,
   deadline, plain water, reminder), hosting, verdict card page + OG
   image and WhatsApp preview (§9), the 10–15 s brain animation and
   replay, sudden death, a group-level how-it-works page, moderation,
   appeal-bypass prevention, production-host timing, stack decision
   (§11).
   **Exit:** 20 real cases in friends' groups, ≥ half shared onward.
4. **Phase 3** — public defender, group bets, case history, verdict
   themes, public "what the fly likes" stats (group-level only, §2.3).

## 13. Open questions (resolve in POC → `DECISIONS.md`)

- Letter → GRN group table (measured valence) and its balance.
- ~~Thresholds~~ — resolved 2026-10-24: 5% gap, 8 flips, hunger 0.8,
  froze 6 Hz (DECISIONS.md).
- ~~Rename "Went for food"~~ — resolved 2026-10-25: "lunch break"
  (הבורר יצא להפסקת צהריים), §7.
- **"Brain overload" as an MVP special outcome?** A whole-brain runaway
  (> 4,000 active neurons) is a real signal of the simulated brain,
  unlike Fled (GF never fires on its own). Arousal is capped below it in
  POC (0.45); an MVP could allow it rarely and show it as its own
  outcome. Decide in MVP planning.
- FlyWire data license terms for possible commercial use.
- ~~Publish the mapping table?~~ — resolved 2026-10-25: **never
  published**; group-level only (§2.3).
- 2B stack (§11): keep the 2A stack on a server or move to the table.

## 14. Phase 2A — Local UI POC

Runs on the workstation only (FastAPI + static HTML page + SQLite, §11).
There are no cases, links, tokens or deadlines: one person types both
sides on one screen. Each **hearing** is one stored row.

1. **Input screen.** An optional **topic** (what the argument is about)
   is shown on the verdict only and is **never fed to the fly**. Each
   side has a **name** and an **argument**. The argument rules are as in
   §3 / §4.1: at least 10 Hebrew letters after normalization, at most
   280 chars; the server checks the same rule.
2. **Mood.** A random hearing seed (stored) gives the mood (§5, simulated
   wait) and drives the simulation. The user never chooses it.
   "Arousal" is shown as **irritability** (עצבנות).
3. **Waiting screen (~7 s).** The order is presentation only: the two
   tastings run in parallel.
   1. The drawn mood, as one story line.
   2. "Tasting side A's argument".
   3. "Tasting side B's argument".
   4. "Deliberating", which loops until the result arrives.
   Something always moves, so it never looks stuck.
4. **Verdict screen.** Courtroom in front: a judge fly, Hebrew legal
   wording, the §7 headline with the topic, and an appetite meter per
   side. The fly art is a placeholder (emoji or simple SVG) until the
   real art arrives.
5. **Appeal.** One per hearing. It reruns the same arguments with a new
   random seed, which gives a new mood (and a new noise draw). If the
   winner changes, it shows "הערעור התקבל!"; otherwise "הערעור נדחה.
   הפסק סופי". The appeal hearing is stored with `appeal_of` = the
   original hearing and has no appeal button. Re-entering the same text
   to get around the limit is accepted in 2A.
6. **"What happened in the brain?"** A button opens the lab view. It is
   fetched on demand from `GET /hearing/{id}/brain`. The summary is
   stored per hearing when the hearing runs; it is never recomputed and
   never holds raw spikes. It contains:
   - MN9 rate over time for each tasting (50 ms bins);
   - activation per taste **group** (never per letter);
   - the mood values, seed, `sim_version` and platform.
   Line shown: "140K neurons of a real fly brain, no AI."
7. **Retention.** Hearings (appeals included) are deleted after 7 days by
   a cleanup that ships with the API, so it carries over to a server.
8. **Out of scope:** server/hosting, WhatsApp sharing and link previews,
   appeal-bypass prevention, production timing (all 2B).

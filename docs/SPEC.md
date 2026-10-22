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
   and stored; the verdict card always reads the stored result.
3. **Transparent.** The verdict card shows what the brain did. There's a
   public "how it works" page.
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
   The table is fixed in code (`borer_sim/taste.py`).
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
- `arousal` ∈ [0, 1] — seeded from case id. Sets background noise →
  more flee / dither.

**Effects:**
- Hunger raises gain of the MN9-exciting GRN groups.
- Arousal increases background spike noise.

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
  - `giant_fiber_fired` — bool, GF spiked in either tasting (escape
    circuit)
- **Replay.** Per-region activity in 20 ms frames, saved for animation.
- **Performance target.** ≤ **15 s per hearing** (both tastings).
  Measured 8.87 s on the workstation (2 processes × 1 thread). The
  subcircuit (P1-10) gives no speed-up and is not used.

## 7. Outcomes

First matching row wins. `gap` as defined in §6. Thresholds calibrated
in POC.

| Outcome        | Condition                                   | Card headline (HE)                  |
|---              |---                                           |---                                   |
| Fled           | Giant Fiber fired in either tasting          | הזבוב עזב את האולם                   |
| Froze          | both tastings' MN9 (`A`, `B`) < 2 Hz         | שתי הטענות לא עניינו את הזבוב       |
| Went for food  | `hunger > 0.8` and `gap < 5%`                | יש דברים חשובים מהוויכוח שלכם        |
| Dithered       | `direction_flips ≥ 3` and `gap < 5%`         | הזבוב קרוע                          |
| Win            | `gap ≥ 5%`                                   | הזבוב פסק לטובת {name}              |
| Plain tie      | otherwise                                    | אין הכרעה                           |

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

Supersedes any earlier version of the spec.

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
     outcome (Fled / Froze / Went for food / Dithered) ≤ 15%.
   - **Input quality:** MN9 range continuous (≤ 50% of tastings in any
     band 10% of the range wide); |Spearman ρ| < 0.5 between
     per-argument MN9 and length, and the ד/ב/ש count; the longer
     argument wins 40–60% of decided hearings, measured over **all
     pairs** of the argument set (DECISIONS.md 2026-10-22, 0.6.0);
     runaway (> 4,000 active neurons) in < 2% of tastings.
   - hearing ≤ 15 s
   - RAM fits in 12 GB (ideally much less).
2. **MVP** — full flow, card, OG preview, animation, all tie types, sudden
   death, how-it-works page.
   **Exit:** 20 real cases in friends' groups, ≥ half shared onward.
3. **Phase 3** — public defender, group bets, case history, verdict
   themes, public "what the fly likes" stats.

## 13. Open questions (resolve in POC → `DECISIONS.md`)

- Letter → GRN group table (measured valence) and its balance.
- Thresholds (5% gap, 3 flips, hunger 0.8, froze 2 Hz).
- Rename the "Went for food" outcome — every argument is food now
  (MVP copywriting).
- FlyWire data license terms for possible commercial use.
- Publish the mapping table openly or let players discover it?

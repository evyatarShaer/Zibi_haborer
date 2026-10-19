# HaBorer (הבורר) — Spec

> Source of truth for product decisions. Change decisions here via a PR with
> an entry in `DECISIONS.md`.

## 1. Product

A WhatsApp-shared web game. Two people argue; a simulation of a real fruit-fly
brain (FlyWire connectome, ~140k neurons) decides who wins. Each side writes
their argument from their own phone. Arguments become "smells" fed to the
fly's olfactory receptors; the fly turns toward one side.

It's a fly, not a judge — the humor is part of the product.

**Goal:** fun first. Revenue is a bonus.

## 2. Principles

1. **The fly decides.** No AI/LLM in the decision path, verdict text, or
   moderation. (Using AI to *write code* is fine.)
2. **Deterministic.** Same case + same arguments + same `sim_version` →
   bit-identical result. All randomness is seeded.
3. **Transparent.** The verdict card shows what the brain did. There's a
   public "how it works" page.
4. **Fair.** Arguments hidden until both are submitted. Which side goes to
   the left vs. right antenna is a seeded coin flip per case.
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

## 4. "Smell of words" (argument → receptor input)

1. **Normalize.** Strip niqqud and duplicate spaces; final letters → regular
   (ך→כ, ם→מ, ן→נ, ף→פ, ץ→צ). Count only the 22 Hebrew letters plus `!` and
   `?`. Everything else counts only toward length. **Max 280 chars.**
2. **Map.** Each Hebrew letter maps to one fixed olfactory glomerulus
   (receptor type) out of ~50. Pool roughly balanced: ~1/3 attractive, ~1/3
   aversive, ~1/3 neutral — based on known biology. The mapping table is
   decided in the POC and fixed in code.
3. **Intensity.** Firing rate per glomerulus comes from letter frequency.
4. **Punctuation.**
   - `!` → CO₂ glomerulus (**V**, aversive).
   - `?` → geosmin glomerulus (**DA2**, aversive).
   - Both capped.
5. **Length.** Logarithmic gain on overall intensity. Too much can turn
   aversive.
6. **Adaptation / saturation (per receptor):**
   `r = r_base + r_max * f / (f + K)` — spamming one letter doesn't work.
7. **Side assignment.** Side A → left or right antenna ORNs by seeded coin
   flip; side B → the other.

## 5. Fly mood (modeled layer on top of the connectome)

> We say this publicly: it's an *added* layer, not from the connectome.

- `hunger` ∈ [0, 1] — seeded from case id; rises while waiting
  (**+0.1 / hour** from case open until both submitted, capped at 1).
  Shown in UI ("the fly has been hungry for 3 hours").
- `arousal` ∈ [0, 1] — seeded from case id. Sets background noise →
  more flee / dither.

**Effects:**
- Hunger raises gain of attractive receptors.
- Arousal increases background spike noise.

## 6. Simulation & readout

- **Model.** Whole-brain leaky integrate-and-fire (LIF), following
  Shiu et al. 2024 (*Nature*). Weights from FlyWire synapse counts, sign
  from predicted neurotransmitter.
- **Data version.** FlyWire **v783**.
- **Input.** Seeded Poisson spikes in ORNs at computed rates.
- **Duration.** 1–2 s simulated.
- **Readout.** Left vs. right turning descending neurons (e.g. DNa02
  family — *verify in POC*). 50 ms bins. Steering signal:
  `(L − R) / (L + R)`.
- **Metrics (per run):**
  - `margin` — winner's share of total turning drive
  - `decision_time_ms` — when cumulative steering crosses threshold and
    stays
  - `direction_flips` — number of sign flips in steering
  - `active_neurons` — count of neurons that spiked
  - `deciding_neuron` — most-spiking winning-side DN + its FlyWire id
  - `giant_fiber_fired` — bool (escape circuit)
- **Replay.** Per-region activity in 20 ms frames, saved for animation.
- **Performance target.** ≤ **15 s per run**. If too slow: subcircuit
  (neurons within N hops on paths from ORNs to turning DNs).

## 7. Outcomes

First matching row wins. Thresholds calibrated in POC.

| Outcome        | Condition                                   | Card headline (HE)                  |
|---              |---                                           |---                                   |
| Fled           | Giant Fiber fired                            | הזבוב עזב את האולם                   |
| Froze          | total turning-DN activity below threshold   | שתי הטענות לא עניינו את הזבוב       |
| Went for food  | `hunger > 0.8` and `gap < 5%`                | יש דברים חשובים מהוויכוח שלכם        |
| Dithered       | `direction_flips ≥ 3` and `gap < 5%`         | הזבוב קרוע                          |
| Win            | `gap ≥ 5%`                                   | הזבוב פסק לטובת {name}              |
| Plain tie      | otherwise                                    | אין הכרעה                           |

Track outcome frequencies globally; show rarity on the card.

## 8. Side B doesn't answer

- **Reminder button.** `wa.me` link with prefilled message.
- **Deadline passes.** Side B gets "clean air" (baseline receptor rates
  only); simulation runs normally. Outcome described as "lost to silence".
- **Public defender** — Phase 3, not MVP. Anyone with the link can write
  for B after half the window elapses.

## 9. Verdict card

Page + 1200×630 OG image.

**Shows:** topic, names, winner or tie type, margin + L/R bar, decision
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
- **Run:** `id`, `case_id`, `round`, `side_assignment`, `input_rates`
  (jsonb), `metrics` (jsonb), `outcome`, `replay_url`, `sim_version`,
  `duration_ms`.
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
   - different texts → different verdicts
   - over 1,000 random argument pairs each side wins ~50%
   - run ≤ 15 s
   - RAM fits in 12 GB (ideally much less).
2. **MVP** — full flow, card, OG preview, animation, all tie types, sudden
   death, how-it-works page.
   **Exit:** 20 real cases in friends' groups, ≥ half shared onward.
3. **Phase 3** — public defender, group bets, case history, verdict
   themes, public "what the fly likes" stats.

## 13. Open questions (resolve in POC → `DECISIONS.md`)

- Letter → glomerulus mapping table and its balance.
- Thresholds (5% gap, 3 flips, hunger 0.8).
- FlyWire data license terms for possible commercial use.
- Publish the mapping table openly or let players discover it?

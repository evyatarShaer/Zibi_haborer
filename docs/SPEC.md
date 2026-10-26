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
   are kept **7 days**, then deleted (§14.8, §15.8).
3. **Transparent.** The verdict card shows what the brain did. There's a
   public "how it works" page. Everything shown is **group-level only**:
   the letter → GRN table is never published (not in the UI, a "how it
   works" page or an API response; DECISIONS.md 2026-10-25).
4. **Fair.** Each side writes blind: arguments are hidden until both
   are submitted (§3). Each argument is tasted separately, on both sides
   of the mouth, with the hearing's seed, so swapping the sides swaps the
   result exactly.
5. **Humor without humiliation.** Mock the dispute, not the loser.
6. **WhatsApp-first.** Mobile, link-based, no sign-up, good link preview.

## 3. User flow

Phase 2B (decided 2026-10-25; details in §15). Each side writes **blind**
and has a **personal link** (§15.1).

1. **Open a case.** Side A enters a topic, their own name, the other
   side's name and their argument. A gets their personal link and a
   "send to the other side" button. The button opens WhatsApp with B's
   link, which has a teaser preview (§9).
2. **B's turn.** B opens their link and sees the topic and the names,
   **never A's argument**, then writes their own. The first device to
   open B's link becomes B; any later device sees "התיק כבר בטיפול"
   (§15.1). B has **3 hours** from
   case open. A's link shows that the court is waiting for B. **After
   1 hour** A gets a "nudge again" button, which opens WhatsApp with a
   ready message and B's link. There are no push notifications.
3. **Hearing.** It runs when B submits, or at the deadline against
   plain water (§8).
   - B watches the waiting story and the verdict **live**, then shares
     with a "send the verdict" button (the public card link).
   - When A opens their link, they get the **same story as a replay**
     from stored data, then the verdict.
   - Anyone else (the public card) goes straight to the verdict.
4. **Appeal.** Each side may appeal once, within 3 hours of the latest
   verdict (§15.4).

Sudden death was dropped on 2026-10-25 (DECISIONS.md).

**Argument rule:** an argument needs **at least 10 Hebrew letters** (after
§4.1 normalization) to be submitted — a deterministic check in the UI,
no AI. The simulation still handles any text safely (§4.6). Names, topic
and arguments also pass the offensive-word filter (§15.5).

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

- `hunger` ∈ [0, 1] — a base draw U(0, 0.4) from the hearing seed,
  plus **+0.25 / hour of real wait** (SIM_VERSION 0.9.0, P2B-1 pick).
  - The wait runs from case open until B submits. No wait counts past
    the 3 h deadline, so a no-show counts 3 h.
  - Hunger is capped at 1 and shown in the UI ("the fly has been hungry
    for 3 hours").
  - The lunch break (hunger > 0.8) is possible only after 1.6 h of
    waiting: ~1–3% of cases for typical-to-slow players (POC_REPORT
    P2B-1).
  - A no-show never gets one: water barely drives MN9, so A wins by
    forfeit (DECISIONS.md 2026-10-26).
- `arousal` ∈ [0, 0.45] — seeded from case id (uniform; capped at 0.45
  because runaways appeared only from 0.48, DECISIONS.md 2026-10-24).
  Sets background noise →
  more dither (and the odd changed verdict).

**Effects:**
- Hunger raises gain of the MN9-exciting GRN groups (drive above
  baseline × (1 + 0.5 · hunger)).
- Arousal increases background spike noise (random-sign 2 mV kicks to
  every neuron at arousal × 10 Hz, so ≤ 4.5 Hz; 20 Hz ignites runaways).
- **Hearing without a waiting time** (Phase 2A only, both sides typed
  at once; 2B uses the real wait): the wait is drawn from the hearing
  seed, ≈ Exp(2 h), capped at the 3 h deadline, and hunger follows the
  rule above. The balance run (`validation.balance`) uses this
  distribution: at 0.1 / h P1-9 measured lunch break ≈ 1.7%; at
  0.25 / h it is re-measured for 0.9.0. The user never chooses the
  mood.
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
- **Replay.** The stored MN9 bins (brain summary) drive the story's
  meters and A's replay (§15.6). No per-region frames are stored.
- **Performance target.** ≤ **15 s per hearing** (both tastings).
  Measured 8.87 s on the workstation (2 processes × 1 thread); the
  production host (ARM) is measured in 2B. The
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
the gap is < 5%. The topic, if given, is shown on a separate line
above the headline: "התיק: {topic}" (§14.4). Every outcome except
Froze shows an appetite meter per side (A vs B MN9 rate). On Froze the
meters are hidden (2026-10-25). A no-show hearing has its own headline
(§8).

Rarity on the card is not in 2B (§13).

## 8. Side B doesn't answer

- **Nudge.** After 1 hour, A's link shows a "nudge again" button. It
  opens WhatsApp (`wa.me`) with a ready message and B's link.
- **Deadline (3 h from case open).** A's argument is tasted against
  **plain water** (baseline GRN rates only, the same input as a text
  with no Hebrew letters). The simulation runs normally, with hunger
  from the full 3 h wait (§5).
  - Headline: **"הזבוב העדיף מים"** when water wins (Win or Dithered
    for side B).
  - Otherwise **"הצד השני לא התייצב לדיון"**.
  - Only A may appeal a no-show (§15.4).
- **Public defender** — Phase 3, not MVP. Anyone with the link can write
  for B after half the window elapses.

## 9. Verdict card

Three views of a case (§15.1):

- **Personal page** (A's or B's link): the story (live or replay), the
  verdict, both arguments, the history, the appeal button while
  allowed, "send the verdict", the brain view (§15.7; parties only) and
  a small "this link is personal" note.
- **Public share card** (page + 1200×630 OG image): topic, names, the
  final verdict and the history (verdict → appeal accepted → appeal
  rejected). **No arguments** and **no brain view**, on the page or in
  the image. Buttons: new case, report (§15.5).
- **Teaser** (the preview of B's link): only the fly and the topic, with
  no verdict, so nothing is spoiled.

OG tags are rendered server-side (WhatsApp's crawler runs no JS). Images
are drawn with Pillow, with correct RTL Hebrew shaping.

Not in 2B (§13): template sentences, rarity, decision time, direction
flips, deciding neuron id and the mini brain map.

## 10. Data model

Phase 2B, SQLite (§11). The 2A `hearing` table (§14) grows into:

- **case:** `id`, `created_at`, `deadline_at` (created + 3 h), `topic`,
  `name_a`, `name_b`, `text_a`, `text_b` (null until B submits; null for
  a no-show = plain water), `b_submitted_at`, `token_a_hash`,
  `token_b_hash`, `b_device_hash` (the first device to open B's link),
  `ip_hash` + day (rate limit), `status` (`waiting`|`hearing`|`decided`|`no_show`),
  `hidden_at` (set by a report or the admin), `shared_at` (first "send
  the verdict" tap; it also bumps the `case_shared` counter once).
- **hearing:** `id`, `case_id`, `n` (0 = verdict, 1–2 = appeals; ≤ 3 per
  case), `appealed_by` (`A`|`B`|null), `seed`, `wait_h`, `hunger`,
  `arousal`, `status`, `metrics`, `outcome`, `winner`, `brain` (MN9 bins,
  mood, seed, version, platform; no taste classes), `sim_version`,
  `platform`, `duration_ms`, `created_at`.
- **report:** `id`, `case_id`, `created_at`.
- **counter:** `day`, `event`, `count`. These are aggregate numbers with
  no case data or ids. They survive the 7-day deletion so that the 2B
  exit criterion can be measured (§12).

Everything except `counter` is deleted 7 days after case open.

**No user accounts.** A side is identified by the token in its personal
link. Only the token's hash is stored.

## 11. Tech stack (FREE only)

Decided for Phase 2B on 2026-10-25 (DECISIONS.md). This replaces the
2026-10-19 table: no Vercel, Neon, Next.js, R2 or Postgres queue. It is
the 2A stack (§14), moved to a server.

| Layer          | Choice                                                                             |
|---              |---                                                                                  |
| Simulation     | Python 3.12 + PyTorch sparse (`borer_sim`), 2 tasting processes × 1 thread          |
| Data           | FlyWire v783 as Parquet, loaded in memory                                          |
| API + pages    | FastAPI (`borer_api`), serving the static page and server-rendered OG tags         |
| Frontend       | Static HTML + ES modules (Hebrew, RTL, no framework), as in 2A                     |
| DB             | SQLite file on the server; 7-day data, so **no backups**                            |
| Queue          | In process: one courtroom, up to 3 waiting (§14.7)                                  |
| OG images      | Pillow, with RTL Hebrew shaping                                                    |
| Animation      | The ~7 s courtroom waiting story; meters fill from stored MN9 bins (§15.6)         |
| Live status    | Polling, as in 2A                                                                  |
| Host           | Oracle Cloud Always Free ARM (Ampere A1), Always Free resources only               |
| HTTPS          | Caddy (automatic Let's Encrypt certificates)                                       |
| Domain         | A free subdomain (e.g. DuckDNS) for now                                            |
| Moderation     | Hebrew offensive-word filter + 20 new cases/day per IP + report + admin (§15.5)    |

Determinism stays per platform (§2.2): verdicts on the ARM host need not
match the x86 workstation bit for bit. Production-host timing and an ARM
determinism check are 2B tasks.

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
3. **Phase 2B — MVP (shareable / server)** (§15):
   - the two-device flow: blind arguments, personal links, a 3 h
     deadline, a nudge after 1 h, plain water at the deadline (§3, §8);
   - hunger from the real wait (§5);
   - live reveal for B and replay for A;
   - appeals: once per side, up to 3 hearings per case;
   - the public card + teaser + OG images (§9);
   - meters that fill from the MN9 curves;
   - the brain view without taste classes, and the how-it-works page
     with credits;
   - moderation;
   - 7-day retention and the expired-link page;
   - hosting on Oracle Always Free + Caddy + a free subdomain (§11);
   - production-host timing.
   **Exit:**
   - **20 real cases** in friends' groups, **≥ half shared onward**: of
     the decided cases, at least half had "send the verdict" tapped at
     least once (server-side counter, §10).
   - On the production host: hearing ≤ 15 s (submit → verdict) and
     bit-identical determinism.
4. **Phase 3** — public defender, group bets, case history, verdict
   themes, public "what the fly likes" stats (group-level only, §2.3).

## 13. Open questions (resolve → `DECISIONS.md`)

- Letter → GRN group table (measured valence) and its balance.
- ~~Thresholds~~ — resolved 2026-10-24: 5% gap, 8 flips, hunger 0.8,
  froze 6 Hz (DECISIONS.md).
- ~~Rename "Went for food"~~ — resolved 2026-10-25: "lunch break"
  (הבורר יצא להפסקת צהריים), §7.
- ~~"Brain overload" as an MVP special outcome?~~ — resolved
  2026-10-25: **not in 2B**. A whole-brain runaway (> 4,000 active
  neurons) is a real signal, unlike Fled; arousal stays capped below it
  (0.45). It may come back after 2B.
- FlyWire data licence (CC-BY-NC) for any commercial use. The credit is
  on the how-it-works page (§15.7).
- ~~Publish the mapping table?~~ — resolved 2026-10-25: **never
  published**; group-level only (§2.3).
- ~~2B stack (§11)~~ — resolved 2026-10-25: the 2A stack on Oracle
  Always Free ARM + Caddy + a free subdomain.
- ~~Class-level leak in the brain view~~ — resolved 2026-10-25: the
  taste-class bars are removed (§15.7).
- ~~Lunch break growth rate~~ — resolved 2026-10-26: **0.25 / h**
  (P2B-1). No-shows stay brain-decided, with no special rule.
- ~~Appeal hunger~~ — resolved 2026-10-26: the case's own wait, with a
  fresh random start.
- ~~No-show display and appeal~~ — resolved 2026-10-26: "הזבוב העדיף
  מים" when water wins; only A may appeal (§8).
- ~~Reports~~ — resolved 2026-10-26: a report hides everything,
  personal pages included.
- ~~B's link in a group~~ — resolved 2026-10-26: the first device to
  open it becomes B; later devices see "התיק כבר בטיפול".
- ~~Brain view on the public card~~ — resolved 2026-10-26: parties only.
- ~~Rate limit~~ — resolved 2026-10-26: 20 new cases per day per IP.
- **Not in 2B; maybe later:** template sentences, rarity, decision time,
  direction flips, deciding neuron and the mini brain map on the card
  (§9); analytics beyond the server-side counters.

## 14. Phase 2A — Local UI POC

Done (gate passed 2026-10-25). Phase 2B (§15) changes items 2
(real wait), 5 (appeals) and 6 (no taste classes) on the server.

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
   wording, the §7 headline, and an appetite meter per side. The topic
   sits on its own line above the headline, "התיק: {topic}", and the
   line is hidden when there is no topic. The fly art is a placeholder (emoji or simple SVG) until the
   real art arrives.
5. **Appeal.** One per hearing. It reruns the same arguments with a new
   random seed, which gives a new mood (and a new noise draw, by design,
   approved 2026-10-25). If the
   winner changes, it shows "הערעור התקבל!"; otherwise "הערעור נדחה.
   הפסק סופי". The appeal hearing is stored with `appeal_of` = the
   original hearing and has no appeal button. Re-entering the same text
   to get around the limit is accepted in 2A.
6. **"What happened in the brain?"** A button opens the lab view. It is
   fetched on demand from `GET /hearing/{id}/brain`. The summary is
   stored per hearing when the hearing runs; it is never recomputed and
   never holds raw spikes. It contains:
   - MN9 rate over time for each tasting (50 ms bins);
   - activation per taste **class** (GRN sub-class: sugar, bitter,
     water, ...; never per letter or per GRN group, since a GRN group is
     fed by one letter);
   - the mood values, seed, `sim_version` and platform.
   Line shown: "140K neurons of a real fly brain, no AI."
7. **One courtroom.** One hearing runs at a time, and up to 3 more
   wait (status `queued`, visible on `GET /hearing/{id}`). Beyond that
   the API answers 503 with "הזבוב עסוק בתיקים אחרים כרגע. נסו שוב בעוד
   דקה".
8. **Retention.** Hearings (appeals included) are deleted after 7 days by
   a cleanup that ships with the API, so it carries over to a server.
9. **Out of scope:** server/hosting, WhatsApp sharing and link previews,
   appeal-bypass prevention, production timing (all 2B).

## 15. Phase 2B — MVP (shareable / server)

Decided on 2026-10-25 (DECISIONS.md, one entry per point). Builds on 2A
(§14): the same `borer_sim`, `borer_api`, `web/` and SQLite, now on a
server (§11). The flow is in §3, the no-show in §8, the card in §9 and
the data model in §10.

1. **Links.**
   - Each side has a **personal tokenized link**. Only personal links
     show the arguments and the appeal button. Each carries a small
     "this link is personal" note.
   - B's link is the one A sends. Its WhatsApp preview is the **teaser**:
     the fly and the topic only, no verdict.
   - The **public share card** (from "send the verdict") shows the
     topic, names, the final verdict and the history, but **no
     arguments**.
   - Tokens are unguessable. Only their hashes are stored.
   - **First opener is B.** The first device to open B's link is bound
     to it (cookie). Any other device gets "התיק כבר בטיפול".
     - The binding happens through the page's script (an API call), not
       on the HTML request, so WhatsApp's preview crawler (no JS) never
       claims B.
     - A device already bound as A is never bound as B: A can tap B's
       link safely.
2. **Blind writing.** B never sees A's argument before submitting. No
   API response or page for B's token contains `text_a` while the case
   is `waiting` (test).
3. **Mood.** Hunger follows the **real wait**, case open → B submits
   (3 h for a no-show; §5). This replaces the simulated wait of §14.2.
   Arousal is drawn from the hearing seed, as before. The growth rate
   is set in P2B-1 (§5).
4. **Appeals.**
   - Each side may appeal **once**, within **3 hours of the latest
     verdict**.
   - Every appeal is judged on the **original arguments** with a fresh
     seed and a fresh mood. **Appeal hunger:** the case's own wait
     (case open → B submits, 3 h for a no-show), with a fresh U(0, 0.4)
     start drawn from the appeal's seed.
   - The **latest verdict is final**. There are at most **3 hearings per
     case** (the verdict + one appeal per side).
   - **No-show:** only A may appeal.
   - An appeal is "accepted" if its winner differs from the previous
     verdict's winner. A non-win outcome counts as "no winner".
   - The card shows the history, e.g. verdict → appeal accepted → appeal
     rejected.
   - The appellant watches the appeal live; the other side gets it as a
     replay.
5. **Moderation (no AI).**
   - **Input filter:** a Hebrew offensive-word list, checked on the
     topic, the names and the arguments after §4.1 normalization. A
     match is a **soft block**: the text is not submitted, and a
     fly-themed message asks the user to rephrase. The owner supplies
     the list.
   - **Report:** a button on the public card. One report **hides the
     whole case immediately** (`hidden_at`): the public card and both
     personal pages show the generic "case closed" page.
   - **Rate limit:** 20 new cases per day per IP (a hashed IP, deleted
     with the case). Beyond that, a fly-themed message.
   - **Admin:** a command on the server lists reported cases and
     deletes or restores one.
6. **Animation.** The ~7 s courtroom waiting story (§14.3) stays. The
   appetite meters fill **live from the stored MN9 curves**, as
   cumulative rate over the tasting. There are no neuron graphics. **On
   a Froze verdict the meters are hidden.**
7. **Disclosure.**
   - The brain view is for **parties only** (personal links), never on
     the public card. It loses the **taste-class bars**; they are neither
     stored nor sent. It keeps the MN9 curves, the mood, the seed,
     `SIM_VERSION` and the platform. This closes the class-level leak
     (DECISIONS.md 2026-10-25).
   - A **"how it works"** page at a general level: FlyWire, words become
     tastes, the fly's mood, no AI. It carries the credit CC-BY-NC
     requires, checked on 2026-10-26 against FlyWire's citation table
     (linked from codex.flywire.ai/about_flywire):
     - co-cite, required: Dorkenwald et al. 2024
       (10.1038/s41586-024-07558-y) and Schlegel et al. 2024
       (10.1038/s41586-024-07686-5);
     - for the parts we use: Zheng et al. 2018 (FAFB,
       10.1016/j.cell.2018.06.019); synapses before July 2025 (v783):
       Buhmann et al. 2021 (10.1038/s41592-021-01183-7) and Heinrich et
       al. 2018 (10.1007/978-3-030-00934-2_36); neurotransmitters:
       Eckstein, Bates et al. 2024 (10.1016/j.cell.2024.03.016);
     - the model: Shiu et al. 2024 (*Nature*).
   - The letter table is never published (§2.3).
8. **Retention.** Everything about a case (hearings, appeals, reports)
   is deleted **7 days after case open**. An expired, deleted or hidden
   link shows one generic page: "case closed, open a new case".
   Aggregate counters (§10) are kept.
9. **One courtroom** as in §14.7. The deadline check runs in the API
   process, and a no-show hearing joins the same queue.
10. **Not in 2B:** sudden death (dropped), "Brain overload", push
    notifications, accounts, backups, the public defender (Phase 3).

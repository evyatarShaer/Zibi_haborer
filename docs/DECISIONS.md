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

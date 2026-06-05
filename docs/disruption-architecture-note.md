# Disruption skills: two layers, do not merge

**Date:** 2026-06-05

Two disruption skill families exist and they are NOT redundant:

| | `skills/disruption-skill/` (from dev branch) | `skills/disruption-handling/` |
|---|---|---|
| Role | **detect-reason-report** — severity scoring, cascade impact, PA-safe payloads, approval gating | **execute** — rebook / cancel / fare-rules actions via agent tools |
| May take actions? | explicitly NO (policy: no rebooking, refunds, cancellations) | yes — that is its purpose |
| Structure | 9 nested sub-skills + shared `disruption-agent-common-policy`, references/schema.md | single SKILL.md (eval-loader compatible) |
| Origin | human-authored on dev (UC-066/068 etc.) | auto-proposed from eval failures, human-edited, eval-gated |
| Eval status | not evaluable by current tool_call tasks (produces reports, not tool calls); future: llm_judge schema-conformance tasks | A/B-gated against the 12-task disruption bank; Δ +0.014 as of 2026-06-05 |

Pipeline view: `detect (disruption-skill) → PA approval → execute (disruption-handling)`.

## Branch hygiene warning

`origin/dev` DELETES `fare-rules`, `hotel-search`, `modify-booking` and trims
`ancillery-skill`/`booking-skill`/`planning-skill` — it predates that work.
**Never merge dev into main wholesale.** The disruption suite was cherry-picked
additively (`git checkout origin/dev -- skills/disruption-skill/`). Dev should
be rebased onto main before any full merge.

---
name: disruption-agent-common-policy
description: Shared policy layer for all Disruption Detection Agent skills (flight-risk, flight-disruption, stay, car, experience, external). Defines the unified severity model, cascade impact schema, PA notification and Action Center formats, ownership and primary-vs-cascading rules, human approval gates, deduplication, escalation, audit trail, fallback behavior, and the standard status lifecycle. Use as the common rules, schemas, and guardrails every disruption skill applies before producing severity, cascade reports, PA payloads, Action Center entries, or approval-gated actions. This skill does not detect disruptions itself.
license: Apache-2.0
metadata:
  version: "0.1.0"
  author: travel-platform
  category: disruption-detection
---

# Disruption Agent Common Policy

## Purpose

Define the common rules every Disruption Detection Agent skill must follow so production behavior is consistent across domains. **This skill does not detect disruptions.** It provides the shared policy, schemas, and guardrails used by the domain skills:

- flight-risk-detection
- flight-disruption-detection
- stay-disruption-detection
- car-disruption-detection
- experience-disruption-detection
- external-disruption-detection

## How to Use This Policy Inside Other Skills

Before producing severity, a cascade report, a PA payload, an Action Center output, or any approval-gated recommendation, apply the shared rules from `disruption-agent-common-policy`:

1. **Severity** — score with the Unified Severity Model below; never invent a different scale.
2. **Cascade** — fill the [Cascade Impact Schema](references/schema.md#cascade-impact-schema), marking unknown layers `unknown`.
3. **Ownership & role** — set `event_role` (`primary` or `cascading`) per the Ownership and Primary-vs-Cascading rules; set `primary_event_ref` for cascades.
4. **Dedup** — compute `dedup_key` and check for an existing primary alert before emitting.
5. **PA payload / Action Center** — emit using the shared [PA Notification Payload Format](references/schema.md#pa-notification-payload-format) and [Action Center Output Format](references/schema.md#action-center-output-format).
6. **Approval gates** — never present rebooking, payment, supplier contact, or itinerary change as done without clearing the required gate.
7. **Status & audit** — advance `status` along the standard lifecycle and write the audit trail.

Canonical guardrail snippets each domain skill should embed:

> Before producing severity, cascade report, PA payload, Action Center output, or any approval-gated recommendation, apply the shared rules from `disruption-agent-common-policy`.

> If this event is only a cascading effect from another domain, do not create a duplicate primary disruption. Report it as a cascade impact and defer ownership to the primary event skill.

## 1. Unified Severity Model

Every skill must use exactly one of `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`, scored by weighing **all** cascading elements together — not the triggering item in isolation.

| Severity | Use when |
|---|---|
| LOW | confirmed but negligible or easily absorbed; no downstream dependency impacted, or recovery already confirmed. Informational. |
| MEDIUM | inconvenience or partial disruption; the trip stays viable, critical itinerary items remain protected, and the traveler is not endangered. |
| HIGH | significant disruption: a booking/connection is missed or at clear risk, downstream cascade is likely, and no recovery is yet confirmed — but a recovery path plausibly exists and traveler safety is not threatened. |
| CRITICAL | traveler safety or emergency/evacuation, traveler stranded with no same-day viable recovery, the trip's purpose is broken with no recovery, or a time-critical medical/business commitment fails. Immediate escalation. |

## 2. Cascade Impact Schema

All skills report downstream impact using the shared per-layer structure across **flight, hotel, car, transfer, activity, MICE, and traveler schedule**. See [references/schema.md](references/schema.md#cascade-impact-schema). A skill fills the layers it can assess and marks the rest `unknown`; it must not overwrite a layer owned by another skill's primary event.

## 3. PA Notification Payload Format

All PA notifications use the unified payload in [references/schema.md](references/schema.md#pa-notification-payload-format), carrying `source_skill`, `event_role`, `severity`, `confidence`, `reasoning`, the `cascade_impact`, `recovery_status` (with `execution_gate`), `pa_guidance`, `status`, `dedup_key`, and `audit`. Specific recommendations are excluded by default (`specific_recommendations_included: false`).

## 4. Action Center Output Format

All Action Center entries use the shared card in [references/schema.md](references/schema.md#action-center-output-format): title, source skill, event role, severity, lifecycle `status`, headline, next step, per-item statuses, `approval_required`, and an `audit_ref`. Render status — not execution — until an approval gate is cleared.

## 5. Ownership Rules (prevent duplicate alerts)

Exactly **one** skill owns the primary event for a given root cause; all others report a cascade only.

| Domain layer | Owning skill |
|---|---|
| Flight delay/cancel/diversion risk | flight-risk-detection / flight-disruption-detection |
| Lodging failure | stay-disruption-detection |
| Rental car & ground transfer | car-disruption-detection |
| Experiences, activities, events, reservations | experience-disruption-detection |
| External events (weather, news/unrest, strikes) | external-disruption-detection |

A skill must not emit a primary alert for a layer it does not own. If it observes impact in another layer, it references that layer as a cascade and defers ownership.

## 6. Primary Event vs Cascading Event Rules

- **Primary event**: the root cause, occurring in the owning skill's domain. The owning skill sets `event_role: primary`, drives recovery, and is the single source of severity for the cause.
- **Cascading event**: a downstream impact in another domain caused by a primary event. The reporting skill sets `event_role: cascading`, sets `primary_event_ref` to the primary, scores severity **only for its own layer's impact**, and does **not** re-classify or re-score the cause.
- If no primary owner exists yet for an observed root cause outside your domain, raise it as `cascading` with `primary_event_ref: unknown` and flag it for the owning skill rather than claiming it.

## 7. Human Approval Gates

No skill may execute **rebooking, payment changes, supplier contact, or itinerary changes** without clearing the required gate:

- `traveler_confirm` — traveler approves the specific option.
- `ops_approval` — Ops approves supplier-expense/compensation or policy-bound actions.
- `emergency_autonomous` — permitted only where policy explicitly grants it (e.g. safety), and always Ops-audited after the fact.

Until a gate is cleared, output is report-and-advise: `major_action_taken: false`, and no action may be described as completed.

## 8. Deduplication Logic

- Compute `dedup_key` from `trip_id` + the root event signature (or `primary_event_ref`) + the domain layer.
- Before emitting, check for an existing alert with the same `dedup_key` or the same `primary_event_ref`. If one exists, **attach/merge** the cascade under the primary instead of raising a new primary alert.
- Suppress repeat PA notifications for the same root event within the dedup window; send an update (status change or severity change) rather than a duplicate.
- One root cause → one primary alert + N cascade references, never N primary alerts.

## 9. Escalation Rules

- `LOW` / `MEDIUM` → notify PA.
- `HIGH` → notify PA and route to Ops when an approval gate is pending.
- `CRITICAL` → immediate notification to PA, Ops, **and** traveler; prioritize safety; do not wait on non-safety dependencies.
- **Time-based**: if a payload sits in `WaitingApproval` past the policy threshold, escalate (PA → Ops → traveler) and record the escalation in the audit trail.

## 10. Audit Trail Requirements

Every disruption record must capture: `detected_at`, source and `confidence`, a `correlation_id` shared across the primary and its cascades, every `status` transition with actor and timestamp, each approval decision, and every executed action and supplier outreach. All execution (including `emergency_autonomous`) must be Ops-auditable after the fact.

## 11. Fallback Behavior (missing supplier / API / status data)

- Never fabricate status, availability, prices, or ETAs. Mark missing layers `unknown` and set `confidence: unverified`.
- Degrade to a best-effort cascade report from what is known; state assumptions and gaps explicitly.
- Never auto-execute on unknown data — hold at `WaitingApproval` or `Assessed` and request the missing input.
- Default to the safe, no-action path; prefer monitoring over speculative recovery.

## 12. Standard Status Lifecycle

```
Detected → Assessed → Reported to PA → Waiting Approval → Approved → Executed → Resolved / Failed
```

- Advance in order; a record may terminate at `Resolved` (success) or `Failed` (execution or approval failed).
- `Waiting Approval` requires a cleared gate (Section 7) before `Approved` → `Executed`.
- Every transition is written to the audit trail (Section 10).

## Golden Examples

Canonical worked examples for the cross-cutting decisions — a severity boundary (HIGH vs CRITICAL), a primary-vs-cascading case (defer ownership, no duplicate), and a deduplication case (attach, don't re-alert) — are in [references/examples.md](references/examples.md). Domain skills should follow these patterns. They are governed fixtures: keep each example's `severity` and `event_role` consistent with the rules above when anything changes.

## Quality Checks

- Severity uses exactly `LOW | MEDIUM | HIGH | CRITICAL`.
- `event_role`, `primary_event_ref`, and `dedup_key` are set; no duplicate primary alert for one root cause.
- No action presented as executed without a cleared approval gate.
- Unknown data is marked `unknown` / `unverified`, never fabricated.
- Status reflects the standard lifecycle and the audit trail is complete.

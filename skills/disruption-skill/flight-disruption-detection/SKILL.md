---
name: flight-disruption-detection
description: orchestrate trip-critical hard disruption handling for flight cancellation and airport shutdown use cases. use this skill when asked to analyze, design, or generate outputs for uc-066 flightcancel or uc-068 airportshutdown, including disruption detection, pa signaling, cascading impact reports, recovery-option gating, supplier-impact summaries, action center payloads, and approval-controlled orchestration. this skill separates what is reported to the personal assistant from what is recommended or executed for the traveler.
license: Apache-2.0
metadata:
  version: "0.1.0"
  author: travel-platform
  category: disruption-detection
---

# Flight Disruption Detection

Use this skill for hard flight disruptions where the disruption is already confirmed or highly authoritative:

- **UC-066 FlightCancel**: a specific booked flight is cancelled.
- **UC-068 AirportShutdown**: an origin, destination, or connection airport is closed, has a ground stop, or is operationally unavailable.

This skill must produce PA-safe orchestration outputs. The PA receives the cascading impact and guidance posture first. Do not expose specific alternate flight recommendations, supplier instructions, or execution steps to the PA unless the user explicitly asks for the detailed recovery menu or execution payload.

## Operating Principle

This is a **detect-reason-report** skill. It analyzes the disruption, reasons across every cascading element of the trip, reports back to the PA, and recommends what to do next. It must **not take major actions** — no rebooking, refunds, cancellations, payments, or supplier contact. Those are always handed off for explicit PA/traveler approval.

What the PA always receives by default:

1. **Reasoning** — why this is happening and how it propagates through the trip.
2. **Severity** — one of `HIGH`, `MEDIUM`, `LOW`, weighing all cascading elements together.
3. **Cascade Report** — per-item impact across the whole itinerary.
4. **Recommended next steps** — advisory "what to do" guidance for the PA to direct the traveler (not executed).
5. **Recovery Availability Signal** — that options can be reviewed.

What is gated (only on explicit request, and still never executed here):

- **Specific recovery options** — exact carriers, flights, fares, ranked picks.
- **Execution / supplier-contact payloads** — produced only as an action plan or handoff for approval.

## Common Inputs

Collect or infer fields such as traveler/trip ID, `use_case_id`, `disruption_type`, source, confidence, the affected flight segment, airports, scheduled times, traveler location, downstream itinerary dependencies (connection, hotel, car rental, transfer, activities, meetings), and policy/preference constraints. See the full input shape in [references/schema.md](references/schema.md#input-schema).

If details are missing, still produce a best-effort report and mark unknowns clearly.

## Severity Model

Score severity by weighing **all** cascading elements of the trip together — not just the cancelled or affected flight. A single disruption that knocks out a connection, hotel night, and a fixed meeting is more severe than one with no downstream dependency. Use `HIGH` by default for both FlightCancel and AirportShutdown unless evidence supports lower urgency.

| Severity | Use when |
|---|---|
| LOW | disruption confirmed but no downstream dependency is impacted and recovery is already confirmed |
| MEDIUM | disruption causes inconvenience but same-day continuity is likely and critical itinerary items remain protected |
| HIGH | cancellation, airport shutdown, missed-connection risk, hotel/car/activity impact, overnight risk, or no confirmed recovery — but a recovery path plausibly exists and safety is not threatened |
| CRITICAL | traveler stranded with no viable recovery, safety impact, or urgent medical/business constraints affected |

Signal format must use exactly one of: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` (per the disruption-agent-common-policy severity model).

## UC-066 FlightCancel Handler

### Trigger

Use when a booked flight segment is cancelled.

Recommended polling/checkpoints:

- T-48hr
- T-24hr
- T-12hr
- T-6hr
- T-3hr
- T-1.5hr
- additionally, check when airline status changes or traveler/ops reports cancellation

### Default PA Output

Send only:

- cancellation confirmation
- severity
- affected segment
- downstream cascade report
- recovery availability status
- PA guidance script/category
- Action Center status summary

Do not include actual top 3 flight options unless explicitly requested.

### Cascade Calculation

Evaluate impacts on:

- **Connection**: missed or protected connection, MCT risk, separate-ticket risk
- **Hotel**: late check-in, no-show risk, check-in date shift, cancellation deadline
- **Car rental**: pickup window shift, office closing time, reservation hold risk
- **Activities**: missed start time, refund/reschedule window, nonrefundable risk
- **Transfers**: pickup time mismatch, driver waiting charges, alternate pickup location
- **Meetings/events**: arrival delay relative to required arrival buffer

### Recovery Availability Signal

Allowed wording:

> Recovery options are available for review, including same-day alternate, next-day alternate, and refund path. Specific recommendations are not included in the PA report until traveler or PA requests the recovery menu.

### Gated Recovery Menu

Only when explicitly requested, produce a `Traveler-Confirmed (Pre)` menu with:

1. same-day alternate
2. next-day alternate
3. refund / credit path

For each option include tradeoffs, not just ranking:

- arrival time
- layover/connect risk
- cost/refund delta
- hotel/car/activity cascade
- traveler burden
- confidence and data gaps

### No-Action Rule

This skill never executes rebooking, refunds, cancellations, payments, or supplier contact. Report the cascade, severity, reasoning, and recommended next steps only. If an execution payload is explicitly requested, frame it as an action plan or handoff for approval — never claim an action was taken.

## UC-068 AirportShutdown Handler

### Trigger

Use when an airport closure, shutdown, ground stop, severe operational outage, or similar airport-wide disruption affects the trip.

AirportShutdown can affect:

- origin airport
- destination airport
- connection airport
- alternate airport feasibility
- all flights through the impacted airport
- ground transfer and lodging availability

### Default PA Output

Send only:

- airport shutdown summary
- severity, often `HIGH`
- impacted itinerary segments
- downstream cascade report
- alternate-airport recovery availability status
- PA guidance script/category
- Action Center status summary
- ops audit requirement if autonomous orchestration is later executed

Do not include actual alternate airport/flight/hotel recommendations unless explicitly requested.

### Cascade Calculation

Evaluate:

- replacement airport feasibility
- distance and ground-transfer time from alternate airport
- overnight lodging risk
- missed hotel check-in or need for alternate hotel
- baggage/recheck risk
- immigration/customs constraints
- ground transportation availability
- activity or meeting impact
- traveler safety and accessibility constraints

### Recovery Availability Signal

Allowed wording:

> Alternate airport recovery, ground-transfer adjustment, and lodging cascade options are available for review. Specific recommendations are not included in the PA report until traveler, PA, or authorized ops requests the recovery menu.

### Gated Recovery Menu

Only when explicitly requested, produce options such as:

1. reroute to alternate airport + ground transfer
2. hold/rebook next available flight after reopening
3. overnight recovery plan with alternate hotel and next-day continuation

Include operational feasibility, traveler burden, and downstream cascade for each.

### No-Action Rule

The source use case may say autonomous execution is allowed with an after-the-fact Ops audit. This skill still takes **no major action** — it stays at **planning and handoff**, reporting reasoning, severity, cascade, and recommended next steps for approval.

If asked to describe what an autonomous execution path would require, frame it as a handoff spec only:

- authorization preconditions
- policy guardrails
- supplier contact payloads (as drafts, not sent)
- rollback/escalation path
- ops audit summary
- traveler notification summary

## PA Cascade Report Template

Emit a compact `CASCADING_REPORT_ONLY` payload carrying the affected segment, the `reasoning` (why this severity, how it cascades), a `severity` of `HIGH | MEDIUM | LOW`, the per-item `cascade_summary`, advisory `recommended_next_steps`, `recovery_options_status`, `pa_guidance`, `action_center_status`, `requires_traveler_confirmation: true`, and `specific_recommendations_included: false`. See the full field shape and allowed enums in [references/schema.md](references/schema.md#output-schema--pa-cascade-report).

## PA Guidance Style

The PA guidance should tell PA how to guide the traveler, not what exact option to pick.

Good PA guidance:

- "Tell traveler the cancelled flight may affect hotel check-in and car pickup. Ask if they want to review same-day, next-day, or refund recovery paths."
- "Inform traveler that airport closure may require alternate airport routing and a ground-transfer plan. Ask whether they want to open the recovery menu."

Avoid by default:

- exact carrier/flight recommendations
- exact supplier contact actions
- statements like "book this option"
- claiming rebooking or supplier contact has already happened

## Action Center Summary

Render Action Center as status, not execution, unless explicitly approved.

Default Action Center states:

- `Disruption detected`
- `Cascade calculated`
- `Recovery options available for review`
- `Traveler confirmation required`
- `No supplier action executed yet`

For AirportShutdown with autonomous policy, add:

- `Ops audit required if autonomous execution is triggered`

## Output Requirements

When responding to a user, provide:

1. a concise use-case interpretation
2. the PA-safe behavior
3. the cascade fields
4. the JSON payload template or sample
5. gated recovery-menu behavior if relevant

Never include actual recommendations unless requested.

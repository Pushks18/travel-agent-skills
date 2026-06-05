---
name: external-disruption-detection
description: Detect external (outside-caused) disruptions that threaten a trip — UC-069 NewsAround (safety incidents, civil unrest, large-scale news events), UC-070 WeatherStorm (severe weather in the trip path), and UC-071 Transport Strike (strike or closure of a booked transport mode) — match them to the traveler's itinerary, compute the cascading impact and a HIGH/MEDIUM/LOW severity, and report to the personal assistant. Use when monitoring or assessing external risk for an itinerary. The skill detects, reasons, and reports by default; specific recovery options are gated as a Traveler-Confirmed menu, and execution (rebooking, supplier contact) happens only after traveler/Ops approval per policy.
license: Apache-2.0
metadata:
  version: "0.1.0"
  author: travel-platform
  category: disruption-detection
---

# External Disruption Detection

Handle disruptions caused by **outside conditions** — not by the traveler's own booking. One skill covers three use cases that share the same flow:

| Use case | Event type | Posture | What's distinctive |
|---|---|---|---|
| UC-069 | NewsAround | Notify | safety incident, civil unrest, or large-scale disruption near origin/destination |
| UC-070 | WeatherStorm | Orchestrate | severe weather in the trip path; polled `T-48h / T-24h / T-12h / T-6h` before departure |
| UC-071 | TransportStrike | Coordinate | strike or closure of a booked transport mode (train, transit, ferry, etc.) |

## Operating Principle

This is a **detect-reason-report** skill. It monitors the external risk, matches it to the itinerary, reasons across every cascading element, and reports to the PA. By default it does **not take major actions**. Recovery is staged:

1. **Report + guidance** — always sent: reasoning, severity, cascade, and what to tell the traveler.
2. **Gated options** — specific recovery options (protective rebook, alternative mode, reschedule, insurance) are surfaced as a **Traveler-Confirmed (Pre)** menu, not as completed actions.
3. **Execution** — rebooking and supplier contact happen **only after traveler/Ops approval**, per the policy `execution_mode`. Emergency autonomous handling is allowed only where policy explicitly grants it, and is always Ops-audited after the fact.

Never claim a rebooking or supplier contact has happened before approval and execution.

## Common Workflow

1. **Monitor external risk** — ingest the risk signal (category, source, confidence, geography, time window). For WeatherStorm, poll `T-48h / T-24h / T-12h / T-6h` before flight departure until detected or the segment passes.
2. **Match risk to itinerary** — find which segments, hotels, cars, transfers, activities, and meetings fall inside the affected geography/time window. A risk only matters where it intersects the traveler's actual plans.
3. **Determine trip impact** — decide whether the matched items are unaffected, at risk, or broken.
4. **Calculate the cascade** — across flight, hotel, car, activities, transfers, meetings, and traveler safety (see Cascade Calculation).
5. **Notify PA / Action Center** — emit the cascade report with reasoning, severity, and guidance.
6. **Show recovery guidance or options** — describe availability; surface specifics only as a Traveler-Confirmed (Pre) menu.
7. **Execute only after approval** — on traveler/Ops approval, execute rebooking and contact each affected onward provider with the revised schedule; render the outcome in Action Center; Ops audits the outreach.

## Severity Model

Score severity by weighing **all** cascading elements together — not just the external event in isolation. Bias higher when traveler safety is involved or the risk is high-confidence with heavy downstream cascade.

| Severity | Use when |
|---|---|
| LOW | risk confirmed but it does not intersect the traveler's locations/dates, or impact is negligible |
| MEDIUM | risk causes inconvenience or partial disruption, but the trip stays viable and the traveler is not endangered |
| HIGH | risk blocks a booked mode/segment or creates significant unrecoverable cascade across the itinerary — but a recovery path plausibly exists and safety is not threatened |
| CRITICAL | risk endangers the traveler's safety, or strands them with no viable recovery |

Signal format must use exactly one of: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` (per the disruption-agent-common-policy severity model).

## Per-Event Handlers

### UC-069 NewsAround (Notify)
Monitor news/advisories near origin and destination. On a Trip-Critical event (safety incident, civil unrest, large-scale disruption), push an alert + impact summary, cross-reference the traveler's planned segments, and where material, note that **protective rebooking** options are available for review.

### UC-070 WeatherStorm (Orchestrate)
On severe weather in the path, compute rebook + insurance + reschedule options and project the downstream cascade across hotel, car, and activities. Surface a **Traveler-Confirmed (Pre)** menu. On approval, execute rebooking and contact each affected supplier (hotel, car-rental, activity provider) with the revised schedule.

### UC-071 TransportStrike (Coordinate)
On a strike/closure for the booked transport mode, push an alert and auto-compute an **alternative-mode** recommendation (alt train, ride, walking + transit combo) with cost and ETA. On approval, contact onward providers (downstream transit, rental, hotel) with the revised ETA to hold/adjust reservations, and render the outcome in Action Center. Ops audits the outreach.

## Cascade Calculation

Evaluate impact on each itinerary element, and how each impact propagates:

- **Flights**: cancellation/diversion likelihood, airspace/airport closure, departure-window overlap with the risk.
- **Hotel**: late check-in, no-show, date shift, relocation if the area is affected.
- **Car rental**: pickup/return location or timing impact; office availability during a strike/closure.
- **Activities**: venue closure, cancellation, refund/reschedule window, safety of attending.
- **Transfers**: blocked mode, reroute time/cost, alternative-mode feasibility.
- **Meetings/events**: ability to arrive safely and on time; whether the trip's purpose stays viable.
- **Traveler safety**: exposure to the hazard, shelter vs. relocate, accessibility/medical exposure, communication/evacuation considerations.

A risk that threatens traveler safety or strands the traveler outweighs schedule-only impacts.

## PA-Facing Report Rules

Send the PA the cascading effect and guidance path, not raw unapproved deal details.

PA payload must include: event type, posture, and severity; a plain-language summary; the cascade across flights/hotel/car/activities/transfers/meetings/safety; whether recovery options are available / in progress / blocked; what the PA should guide the traveler to do next; and the Action Center status.

PA payload must not include: a recovery option phrased as already executed before approval, unconfirmed supplier details, or claims that rebooking/outreach is complete when only proposed.

## Output Template

Emit the system-facing payload carrying `use_case_id`, `event_type`, `posture`, `severity` and `pa_signal` (`HIGH | MEDIUM | LOW`), `confidence`, `reasoning`, `risk_summary`, the per-item `cascade_summary` (including `traveler_safety`), `recovery_status` (with `execution_gate`), `pa_guidance`, the `action_center` block, `ops_audit_required`, `specific_recommendations_included: false`, and `major_action_taken: false`. See the full field shape and allowed enums in [references/schema.md](references/schema.md#output-schema--pa-cascade-report).

## Action Center Summary

Render Action Center as status until execution is approved. Default states: `monitoring`, `needs_traveler_confirmation`, `needs_ops_approval`, `executing`, `completed`, `blocked`. For approved execution, record the supplier outreach so **Ops can audit** it.

## Quality Checks

- Confirm the external risk actually intersects the traveler's locations/dates and booked modes before raising severity.
- State the confidence of the risk signal; never invent advisory levels, weather probabilities, alt-mode costs/ETAs, or availability.
- Surface assumptions and unknowns explicitly.
- Confirm no major action was executed before the required traveler/Ops approval — output reflects report-and-advise until then.

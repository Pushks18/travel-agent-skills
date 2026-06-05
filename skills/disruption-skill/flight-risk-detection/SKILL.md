---
name: flight-risk-detection
description: Detect the risk that a flight will be delayed, cancelled, or diverted — from weather, airport conditions, airspace/ATC flow, airline operations, inbound-aircraft delays, crew/maintenance, strikes, security events, or natural events — and report the cascading impact, reasoning, and a HIGH/MEDIUM/LOW severity to the personal assistant. Use for the FlightDelay / FlightRisk use case when asked to assess, monitor, or report the likelihood and downstream impact of a flight disruption before or as it develops. This skill detects, reasons, and reports; it never takes major actions such as rebooking, cancelling, or contacting suppliers.
license: Apache-2.0
metadata:
  version: "0.1.0"
  author: travel-platform
  category: disruption-detection
---

# Flight Risk Detection

Use this skill for the **FlightDelay / FlightRisk** use case: assess the risk that a booked flight will be delayed, cancelled, or diverted, and report what that risk means for the whole itinerary — before or as the situation develops. Unlike skills that react to a disruption already confirmed, this one weighs the **probability and projected impact** of a flight disruption.

Risk factors that elevate flight delay/disruption likelihood:

- **Weather**: storms, low visibility, snow/ice, wind at origin, destination, or en route.
- **Airport conditions**: congestion, ground stops, capacity programs, closures.
- **Airspace / ATC**: flow control, restrictions, airspace closures.
- **Airline operations**: schedule pressure, aircraft swaps, knock-on delays.
- **Inbound aircraft**: the assigned aircraft arriving late from a prior leg.
- **Crew / maintenance**: crew legality/availability, mechanical or maintenance holds.
- **Strikes / labor**: airline, airport, or ATC labor action.
- **Security / natural events**: airport security incidents, volcanic ash, wildfire smoke.

## Operating Principle

This is a **detect-reason-report** skill. It analyzes the flight risk, reasons across every cascading element of the trip, reports back to the PA, and recommends what to do next. It must **not take major actions** — no rebooking, cancellations, refunds, payments, supplier contact, or itinerary changes. Those are always handed off for explicit PA/traveler approval.

What the PA always receives by default:

1. **Reasoning** — what the risk is, its likelihood, and how it would propagate through the trip.
2. **Severity** — one of `HIGH`, `MEDIUM`, `LOW`, weighing all cascading elements together.
3. **Cascade Report** — per-item impact across the whole itinerary, including traveler impact.
4. **Recommended next steps** — advisory "what to do" guidance for the PA to direct the traveler (not executed).
5. **Monitoring status** — whether the risk warrants continued monitoring as it develops.

What is gated (only on explicit request, and still never executed here):

- **Specific recovery options** — exact rerouting, carriers, or ranked picks.
- **Execution / supplier-contact payloads** — produced only as an action plan or handoff for approval.

## Required Inputs

Collect or infer the trip/traveler identifiers, the **flight** (airline, number, airports, connection, scheduled times), the **risk signal** (category, description, source, confidence, delay likelihood, expected impact, time window), the **itinerary** (connections, hotels, ground transport, activities, meetings), and **traveler context** (current location, accessibility, medical needs, party size, priority). See the full input shape in [references/schema.md](references/schema.md#input-schema).

If details are missing, still produce a best-effort report and mark unknowns clearly. State the confidence of the underlying risk signal.

## Workflow

1. **Detect & qualify the risk**
   - Identify the risk category, the affected flight, and the time window.
   - Record source, confidence (`confirmed`, `probable`, `unverified`), and expected impact (`delay`, `cancellation`, `diversion`). Do not invent likelihoods or facts.

2. **Project the impact on the flight**
   - Estimate whether the flight is likely delayed, cancelled, or diverted, and by roughly how much, given the signal.

3. **Reason through the cascade**
   - For each downstream itinerary element, explain the impact and how it knocks on to later elements.
   - Account for traveler accessibility and medical constraints.

4. **Score severity**
   - Weigh all cascading elements together (see Severity Model).

5. **Report to the PA**
   - Emit the flight-risk cascade report with reasoning, severity, cascade, and recommended next steps.
   - Set monitoring status if the situation is evolving.

6. **Hand off, never execute**
   - If recovery options or execution payloads are requested, produce them as an action plan for approval — never claim an action was taken.

## Cascade Calculation

Evaluate impact on each downstream itinerary element, and how each impact propagates:

- **Connection**: missed or tight connection if the flight is delayed, MCT risk, separate-ticket risk.
- **Hotel**: late check-in, no-show risk, check-in date shift, cancellation deadline.
- **Ground transport**: pickup-window mismatch, driver waiting charges, alternate pickup.
- **Activities**: missed start time, refund/reschedule window, nonrefundable risk.
- **Meetings/events**: arrival delay relative to a required arrival buffer; whether the purpose of travel stays viable.
- **Traveler impact**: rebooking burden, overnight risk, accessibility/medical exposure if stranded.

A risk that strands the traveler or breaks an unrecoverable downstream commitment outweighs schedule-only slippage.

## Severity Model

Score severity by weighing **all** cascading elements of the trip together — not just the flight in isolation. A delay that threatens a connection, a hotel night, and a fixed meeting is more severe than one the trip can absorb. Factor in likelihood and confidence: a high-probability disruption with heavy cascade is `HIGH`; a low-probability signal with no downstream dependency is `LOW`.

| Severity | Use when |
|---|---|
| LOW | risk is low-probability or does not meaningfully affect the schedule, and no downstream dependency is impacted |
| MEDIUM | a delay is plausible and causes inconvenience, but the trip remains viable and critical itinerary items remain protected |
| HIGH | cancellation/diversion likely, missed-connection risk, hotel/car/activity impact, overnight risk, or no confirmed recovery yet — but a recovery path plausibly exists |
| CRITICAL | traveler stranded with no same-day viable recovery, the trip's purpose is broken with no recovery, or a time-critical medical/business commitment fails |

Signal format must use exactly one of: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` (per the disruption-agent-common-policy severity model).

## PA Flight Risk Cascade Report

Emit a compact `CASCADING_REPORT_ONLY` payload carrying the `risk_category`, `expected_impact`, `confidence`, the `reasoning` (why this severity, how it cascades), a `severity` of `HIGH | MEDIUM | LOW`, the `risk_summary` (flight/what/when/source), the per-item `cascade_summary` (including `traveler_impact`), advisory `recommended_next_steps`, `monitoring_status`, `pa_guidance`, `action_center_status`, `requires_traveler_confirmation: true`, `major_action_taken: false`, and `specific_recommendations_included: false`. See the full field shape and allowed enums in [references/schema.md](references/schema.md#output-schema--pa-flight-risk-cascade-report).

## PA Guidance Style

The PA guidance should tell the PA how to guide the traveler, not what exact option to pick or book.

Good PA guidance:

- "Tell traveler a storm system raises the chance their outbound flight is delayed, which would tighten their connection and push hotel check-in; ask if they want rerouting or earlier-flight options reviewed."
- "Inform traveler that an airline operational issue may delay departure; ask whether they want alternate-flight options reviewed while we monitor."

Avoid by default:

- exact carrier/flight recommendations
- exact supplier contact actions
- statements like "book this option"
- claiming any rebooking, cancellation, or supplier contact has happened

## Action Center Summary

Render Action Center as status, not execution.

Default Action Center states:

- `Flight risk detected`
- `Cascade calculated`
- `Severity assigned`
- `Monitoring active` (when the situation is evolving)
- `Traveler confirmation required` (when recovery review is offered)
- `No supplier action executed`

## Quality Checks

- Confirm the risk actually affects the booked flight and intersects the traveler's dates before raising severity.
- State the confidence and likelihood of the risk signal; never invent probabilities, facts, or availability.
- Surface assumptions and unknowns explicitly.
- Confirm no major action was taken — output must reflect report-and-advise only.

## Output Requirements

When responding to a user, provide:

1. a concise interpretation of the flight risk and its likely impact
2. the reasoning across the cascade
3. the severity (`HIGH | MEDIUM | LOW`) and why
4. the cascade fields and recommended next steps
5. the JSON payload template or sample

Never include actual recommendations or take any major action unless explicitly requested, and even then only as an approval handoff.

---
name: stay-disruption-detection
description: Stay disruption detection and PA-guidance workflow for trip-critical accommodation failures. Use this skill when handling hotel shutdown, hotel overbooking or walk, hotel booking cancellation, property closure or renovation, safety or emergency evacuation, or any equivalent lodging disruption where the traveler cannot use the planned property. Use it to classify severity, prepare PA-facing cascade reports, identify equivalent-property recovery paths, route supplier-expense negotiation to Ops approval, and draft Action Center outcomes without exposing unapproved recommendations as final actions.
license: Apache-2.0
metadata:
  version: "0.1.0"
  author: travel-platform
  category: disruption-detection
---

# Stay Disruption Detection

## Purpose

Evaluate and structure **UC-067** stay disruption events where the planned lodging is unavailable or unsafe, and report what that means for the whole trip. The skill produces a PA-facing disruption report, the cascade impact, Ops-approval routing, and Action Center outcome language.

Primary covered events:

- HotelShutDown
- Hotel Overbooking / walk
- Hotel Booking Cancelled
- Property Closure / Renovation
- Safety / Emergency Evacuation

## Operating Principle

This is a **detect-reason-report** skill. It analyzes the lodging disruption, reasons across every hotel-anchored element of the trip, reports to the PA, and routes recovery to Ops for approval. It must **not take major actions** — no rebooking, supplier negotiation as final, compensation commitments, or itinerary changes — until Ops approval is present (or policy explicitly allows emergency autonomous handling).

What the PA always receives by default:

1. **Reasoning** — what failed and how it propagates through the trip.
2. **Severity** — one of `HIGH`, `MEDIUM`, `LOW`, weighing all hotel-anchored dependencies together.
3. **Cascade Report** — per-item impact across hotel, car, activities, transfers, meetings, and special requests.
4. **Recovery posture** — whether an equivalent-property path is available, in progress, pending Ops approval, or blocked.
5. **PA guidance** — what to tell the traveler next.

What is gated (never presented as completed before approval):

- Final supplier negotiations or compensation terms.
- Claims that rebooking or compensation has been executed when it has only been proposed.

## Trigger and Classification

Classify the event as `Trip-Critical` when any of the following is true:

- Traveler cannot check in at the booked property.
- Property is closed, renovated, unsafe, evacuated, or unavailable.
- Hotel walks the traveler because of overbooking.
- Booking is cancelled by the supplier, platform, or property.
- The hotel location anchored onward car pickup, activity pickup, meeting location, or transfer routing.

## Severity Model

Score severity by weighing **all** hotel-anchored dependencies together — not just the lodging itself. A cancellation that also breaks car pickup, a tour, and a meeting location is more severe than one with a clean equivalent replacement. Safety-driven events are always top-urgency `HIGH`.

| Severity | Use when |
|---|---|
| LOW | informational only; no traveler impact. Do not use for confirmed unavailability that affects the traveler. |
| MEDIUM | an equivalent replacement is already confirmed with no cost increase and minimal location impact. |
| HIGH | hotel unavailable before arrival, overbooking/walk, cancellation without a confirmed equivalent replacement, closure/renovation, onward dependencies affected, or no nearby equivalent inventory — but a replacement path plausibly exists |
| CRITICAL | safety/emergency evacuation, traveler already at the property with nowhere to stay, late-night displacement, or a vulnerable/accessibility/family-group traveler stranded with no equivalent inventory |

Signal format must use exactly one of: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` (per the disruption-agent-common-policy severity model).

## Standard Workflow

1. **Detect and normalize the stay disruption.**
   - Capture the original hotel, address, chain/brand, room type, rate, check-in/out dates, loyalty tier, special requests, and cancellation/walk reason. See the full input shape in [references/schema.md](references/schema.md#input-schema).
   - Identify whether the disruption is property-driven, supplier-driven, safety-driven, or traveler-impact-driven.

2. **Build the cascade report** (see Cascade Calculation).

3. **Prepare the equivalent-property recovery path.**
   - Prefer same chain or partner chain, especially preferred Marriott/Hilton tier where applicable.
   - Match property class, room type, location, amenities, accessibility/special requests, and no traveler cost increase where supplier fault applies.
   - Do not describe a property as equivalent if it fails room capacity, accessibility, safety, or location-critical requirements.

4. **Prepare the compensation and supplier-expense position.**
   - Where the disruption is property/supplier caused, ask the original property/supplier to cover a same-rate or upgraded equivalent.
   - Targets: rate protection, room upgrade, transport to the new property, waived fees, loyalty points, resort/parking fee coverage, late check-in guarantee.
   - Mark any unresolved compensation as `OPS_APPROVAL_REQUIRED`.

5. **Route to Ops for approval.**
   - Provide the recommended replacement strategy and supplier-expense terms, with risks, cost delta, traveler inconvenience, supplier responsibility, and urgency.
   - Do not execute rebooking until Ops approval is present unless policy explicitly allows emergency autonomous handling.

6. **After approval, structure execution steps** (as a handoff plan, not a completed action): rebook the replacement, contact the new property with ETA/special requests/loyalty/accessibility/perks, confirm compensation with the original supplier, and cascade the updated location to car-rental, activities, transfers, and other hotel-anchored services.

7. **Render the outcome in Action Center**: status, cascade summary, Ops-approval status, replacement-property status, supplier-contact status, unresolved risks, and traveler-facing next step.

## Cascade Calculation

Evaluate impact on each hotel-anchored element, and how each impact propagates:

- **Check-in feasibility**: arrival ETA vs. the disruption; late-night or pre-arrival displacement risk.
- **Car rental**: pickup/return location or timing tied to the hotel; office hours; relocation distance.
- **Activities/tours**: pickup point, refund/reschedule window, location delta from a replacement property.
- **Transfers**: airport↔hotel reroute impact and added time/cost.
- **Meetings/events**: arrival and location impact relative to a replacement property.
- **Special requirements**: accessibility, family/group capacity, pets — must be preserved by any replacement.
- **Location delta**: distance/time from the original property to the candidate area, airport, meetings, activities, or car pickup.

A disruption that threatens traveler safety or strands the traveler outweighs schedule-only impacts.

## PA-Facing Report Rules

Send the PA the cascading effect and guidance path, not raw unapproved deal details.

PA payload must include: event type and severity, a plain-language disruption summary, the cascade across hotel/car/activities/transfers/meetings/special-requests, whether equivalent-property recovery is available / pending Ops approval / blocked, what the PA should guide the traveler to do next, and the Action Center status.

PA payload must not include: a recommendation phrased as already approved when Ops approval does not exist, unconfirmed supplier negotiation details, or claims that rebooking/compensation is complete when only proposed.

## Output Template

Emit the system-facing payload carrying `use_case_id`, `event_type`, `priority: Trip-Critical`, `severity` and `pa_signal` (`HIGH | MEDIUM | LOW`), `reasoning`, `ops_approval_required`, `major_action_taken: false`, `traveler_state`, the per-item `cascade_report`, `recovery_status`, `pa_guidance`, and the `action_center` block. See the full field shape and allowed enums in [references/schema.md](references/schema.md#output-schema--pa-cascade-report).

## Action Center Summary

Render Action Center as status, not execution. Default states: `needs_ops_approval`, `recovery_in_progress`, `rebooked`, `blocked`.

## Quality Checks

- Confirm the disruption actually prevents use of the planned property before raising severity.
- State the confidence of the disruption signal; never invent availability, rates, or supplier commitments.
- Never describe a replacement as equivalent unless it matches capacity, accessibility, safety, and location-critical needs.
- Confirm no major action was taken without Ops approval — output must reflect report-and-route only.

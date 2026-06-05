---
name: car-disruption-detection
description: Detect rental-car and ground-transfer disruptions and risk for the Disruption Detection Agent — pickup delay or missed window, rental location closed, supplier cancellation, vehicle class unavailable, no-show risk from a delayed flight or late arrival, drop-off delay risk, and ground-transfer provider delay or cancellation. Determine whether the issue is a primary car disruption or a cascade from a flight/hotel/activity delay, compute the itinerary impact and a HIGH/MEDIUM/LOW severity, and report to the personal assistant. The skill detects, reasons, and reports; it does not contact suppliers, rebook, or change payments unless explicitly approved.
license: Apache-2.0
metadata:
  version: "0.1.0"
  author: travel-platform
  category: disruption-detection
---

# Car Disruption Detection

Handle rental-car and ground-transfer disruptions for the Disruption Detection Agent. Covered use cases:

1. Car pickup delay or missed pickup window
2. Rental location closed
3. Car booking cancelled by supplier
4. Vehicle class unavailable
5. No-show risk due to a delayed flight or late arrival
6. Drop-off delay risk
7. Ground transfer provider delay or cancellation

## Operating Principle

This is a **detect-reason-report** skill. It detects the car/transfer disruption or risk, decides whether it is a **primary** car disruption or a **cascade** from another disruption, reasons across the itinerary, and reports to the PA. It must **not take major actions** — no supplier contact, rebooking, vehicle changes, or payment changes — unless explicitly approved. Specific recovery options are surfaced for review; execution happens only on traveler/Ops approval per the policy `execution_mode`.

What the PA always receives by default:

1. **Reasoning** — what the disruption is, whether it is primary or cascading, and how it propagates.
2. **Severity** — one of `HIGH`, `MEDIUM`, `LOW`, weighing all dependent itinerary elements together.
3. **Cascade Report** — per-item impact across pickup, drop-off, onward transport, hotel, activities, meetings, and flight return.
4. **Recovery posture** — whether options are available, in progress, or blocked.
5. **PA guidance** — what to tell the traveler next.

## Trigger Conditions

Detect or raise risk when any of the following is true:

- **Pickup delay / missed window**: the pickup time is at risk or has lapsed.
- **Rental location closed**: the booked branch is closed, relocated, or unreachable.
- **Booking cancelled**: the supplier, platform, or branch cancels the reservation.
- **Vehicle class unavailable**: the booked class cannot be provided (capacity, accessibility).
- **No-show risk**: a delayed flight or late arrival means the traveler reaches pickup after the window or after closing.
- **Drop-off delay risk**: return is at risk of being late (affecting a return flight or fees).
- **Ground transfer delay/cancellation**: a booked transfer provider is delayed or cancels.

For each, set `disruption_origin` to `primary_car` or to the cascading source (`cascading_from_flight` / `_hotel` / `_activity`).

## Severity Model

Score severity by weighing **all** dependent itinerary elements together — not the car booking alone. A missed pickup that also breaks hotel arrival and a fixed meeting is more severe than one with an easy alternative and no dependency.

| Severity | Use when |
|---|---|
| LOW | confirmed but easily absorbed — alternative readily available, no onward dependency, ample buffer |
| MEDIUM | inconvenience or partial disruption, but the trip stays viable and onward items remain protected |
| HIGH | no viable pickup/transfer, onward hotel/activity/meeting broken, return-flight risk from a drop-off delay, or no nearby equivalent vehicle/transfer — but a recovery path plausibly exists |
| CRITICAL | traveler stranded with no viable transport and a broken safety- or time-critical onward dependency (e.g. a missed return flight with no same-day recovery) |

Signal format must use exactly one of: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` (per the disruption-agent-common-policy severity model).

## Cascade Calculation

First classify origin (primary vs. cascading), then evaluate impact on each dependent element and how it propagates:

- **Pickup**: arrival ETA vs. pickup window and location hours; no-show risk; relocation distance to an alternative branch.
- **Drop-off**: late-return risk vs. a return flight or extra-day fees.
- **Onward transport**: whether the car/transfer was the means of reaching the next stop.
- **Hotel**: late or missed arrival if the car/transfer was the route to check-in.
- **Activities / meetings**: pickup point, start time, and location delta if transport slips.
- **Flight return**: a drop-off delay that threatens a return flight.

A disruption that strands the traveler or breaks an unrecoverable onward commitment outweighs schedule-only slippage.

## PA Payload Format

Send the PA the cascading effect and guidance path, not raw unapproved supplier details.

PA payload must include: `event_type`, `disruption_origin`, severity, reasoning, a plain-language summary, the per-item `cascade_summary`, the recovery posture (available / in progress / blocked), `pa_guidance`, and the Action Center status. It must not present any supplier contact, rebooking, or payment change as completed before approval. See the full field shape and allowed enums in [references/schema.md](references/schema.md#output-schema--pa-cascade-report). Input fields are in [references/schema.md](references/schema.md#input-schema).

## Action Center Output

Render Action Center as status, not execution. Default states: `monitoring`, `needs_traveler_confirmation`, `needs_ops_approval`, `executing`, `completed`, `blocked`. Carry a short `headline` and `next_step`. Only move to `executing`/`completed` once approval is present.

## Guardrails (avoid overlap with sibling skills)

- **Own the car/transfer layer only.** This skill reports the car/ground-transfer impact and recovery posture. It does not assess flight delay/cancellation likelihood (that is `flight-risk-detection` / `flight-delay-detection`) or lodging failure (that is `stay-disruption-detection`).
- **When a flight or hotel disruption is the root cause**, treat it as the cascading source: set `disruption_origin` accordingly, reference it as context, and report only the *car/transfer* consequence. Do not re-classify or re-score the upstream flight/hotel event.
- **Defer the upstream signal.** If a flight-risk or stay-disruption report already exists for the same trip event, align to it rather than emitting a competing severity for the root cause; this skill's severity describes the car/transfer impact.
- **No double execution.** Do not contact a hotel/airline already owned by another skill's workflow; limit supplier contact (post-approval) to car-rental and ground-transfer providers.

## Quality Checks

- Confirm the disruption actually affects this trip's car/transfer booking and intersects the traveler's timing before raising severity.
- Classify `disruption_origin` correctly — do not label a flight/hotel-caused issue as a primary car disruption.
- State the confidence of the signal; never invent supplier availability, vehicle classes, costs, or ETAs.
- Confirm no supplier contact, rebooking, or payment change was executed without approval — output reflects report-and-advise until then.

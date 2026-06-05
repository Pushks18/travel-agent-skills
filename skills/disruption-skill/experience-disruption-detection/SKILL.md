---
name: experience-disruption-detection
description: Detect disruptions to booked experiences — tours, attractions, events, shows, excursions, classes, and dining reservations — for the Disruption Detection Agent. Covers provider cancellation, venue closure, event reschedule, missed-start risk from upstream delays, provider no-show or overbooking, reservation cancellation, and capacity or accessibility issues. Determine whether the issue is a primary experience disruption or a cascade from a flight/car/hotel/external delay, compute the itinerary impact and a HIGH/MEDIUM/LOW severity, and report to the personal assistant. The skill detects, reasons, and reports; it does not contact providers, rebook, refund, or change payments unless explicitly approved.
license: Apache-2.0
metadata:
  version: "0.1.0"
  author: travel-platform
  category: disruption-detection
---

# Experience Disruption Detection

Handle disruptions to booked experiences for the Disruption Detection Agent — tours, attractions, events, shows, excursions, classes, and dining reservations. Covered use cases:

1. Activity / tour cancelled by the provider
2. Venue or attraction closed
3. Event cancelled, postponed, or rescheduled
4. Missed-start risk from a delayed flight, car, or hotel cascade
5. Provider no-show or overbooking
6. Reservation cancelled (e.g. dining)
7. Capacity or accessibility issue

## Operating Principle

This is a **detect-reason-report** skill. It detects the experience disruption or risk, decides whether it is a **primary** experience disruption or a **cascade** from another disruption, reasons across the day and the wider trip, and reports to the PA. It must **not take major actions** — no provider contact, rebooking, refunds, reschedules, or payment changes — unless explicitly approved. Specific recovery options are surfaced for review; execution happens only on traveler/Ops approval per the policy `execution_mode`.

What the PA always receives by default:

1. **Reasoning** — what the disruption is, whether it is primary or cascading, and how it propagates.
2. **Severity** — one of `HIGH`, `MEDIUM`, `LOW`, weighing all dependent itinerary elements together.
3. **Cascade Report** — per-item impact across the experience, same-day activities, anchoring transport, dining/reservations, downstream plans, and refund/reschedule posture.
4. **Recovery posture** — whether options are available, in progress, or blocked.
5. **PA guidance** — what to tell the traveler next.

## Trigger Conditions

Detect or raise risk when any of the following is true:

- **Activity/tour cancelled**: the provider cancels a booked tour, excursion, or class.
- **Venue closed**: the attraction or venue is closed, at capacity, or unreachable.
- **Event rescheduled**: a show/event is cancelled, postponed, or moved.
- **Missed-start risk**: a delayed flight/car/hotel cascade means the traveler arrives after a fixed start.
- **Provider no-show / overbooked**: the provider fails to honor the booking.
- **Reservation cancelled**: a dining or timed reservation is dropped.
- **Capacity / accessibility issue**: party size, accessibility, or eligibility can no longer be met.

For each, set `disruption_origin` to `primary_experience` or to the cascading source (`cascading_from_flight` / `_car` / `_hotel` / `_external`).

## Severity Model

Score severity by weighing **all** dependent itinerary elements together — and the experience's role in the trip. A cancelled trip-anchoring or special-occasion experience with no alternative is more severe than a minor, refundable activity with a free later slot.

| Severity | Use when |
|---|---|
| LOW | minor and refundable, easy alternative or later slot, no downstream dependency |
| MEDIUM | inconvenience or partial loss, but the day stays viable and other plans remain protected |
| HIGH | a trip-anchoring or special-occasion experience is lost with no viable alternative, non-refundable value is at risk, or the disruption cascades to same-day transport/dining/downstream plans |
| CRITICAL | an irreplaceable once-in-a-trip occasion (or the sole purpose of travel) is destroyed with no recovery, or a safety/accessibility failure endangers the traveler at the venue |

Signal format must use exactly one of: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` (per the disruption-agent-common-policy severity model).

## Cascade Calculation

First classify origin (primary vs. cascading), then evaluate impact on each dependent element and how it propagates:

- **The experience itself**: lost, partial, reschedulable, refundable; special-occasion or trip-anchoring weight.
- **Same-day activities**: items timed around this one; knock-on to later starts.
- **Anchoring transport**: a car/transfer or pickup booked specifically for this experience (flag for the car/transfer layer, do not re-score it).
- **Dining / reservations**: timed reservations that depend on this experience finishing/starting.
- **Downstream plans**: evening or next-day plans that assumed this experience.
- **Refund / reschedule window**: deadlines and non-refundable exposure.

A disruption that destroys irreplaceable or special-occasion value, or cascades across the day, outweighs a single refundable slot.

## PA Payload Format

Send the PA the cascading effect and guidance path, not raw unapproved provider details.

PA payload must include: `event_type`, `disruption_origin`, severity, reasoning, a plain-language summary, the per-item `cascade_summary`, the recovery posture (available / in progress / blocked), `pa_guidance`, and the Action Center status. It must not present any provider contact, rebooking, refund, or payment change as completed before approval. See the full field shape and allowed enums in [references/schema.md](references/schema.md#output-schema--pa-cascade-report). Input fields are in [references/schema.md](references/schema.md#input-schema).

## Action Center Output

Render Action Center as status, not execution. Default states: `monitoring`, `needs_traveler_confirmation`, `needs_ops_approval`, `executing`, `completed`, `blocked`. Carry a short `headline` and `next_step`. Only move to `executing`/`completed` once approval is present.

## Guardrails (avoid overlap with sibling skills)

- **Own the experience/activity layer only.** This skill reports the experience impact and recovery posture. It does not assess flight risk (`flight-risk-detection` / `flight-delay-detection`), lodging failure (`stay-disruption-detection`), car/transfer disruption (`car-disruption-detection`), or external events like weather/strikes (`external-disruption-detection`).
- **When another disruption is the root cause**, treat it as the cascading source: set `disruption_origin`, reference it as context, and report only the *experience* consequence. Do not re-classify or re-score the upstream event (e.g. a weather closure stays owned by `external-disruption-detection`).
- **Defer to the upstream signal.** If a sibling report already exists for the same root event, align to it rather than emitting a competing severity for the cause; this skill's severity describes the experience impact.
- **No double execution.** Limit post-approval contact to the experience/activity provider; do not contact an airline, hotel, or car supplier owned by another skill's workflow.

## Quality Checks

- Confirm the disruption actually affects this trip's booked experience and intersects the traveler's timing before raising severity.
- Classify `disruption_origin` correctly — do not label a flight/car/hotel/external-caused issue as a primary experience disruption.
- State the confidence of the signal; never invent provider availability, alternative slots, refund terms, costs, or ETAs.
- Confirm no provider contact, rebooking, refund, or payment change was executed without approval — output reflects report-and-advise until then.

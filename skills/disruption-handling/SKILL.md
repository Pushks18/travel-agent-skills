---
name: disruption-handling
description: Respond to airline-caused travel disruptions — use when the traveler reports their flight was cancelled by the airline, a major delay means they need the next available flight, the plane went technical at the gate, they missed a connecting flight because the first leg arrived late, their flight diverted to a different city, or they were involuntarily bumped from an overbooked flight. Covers rebooking onto an alternative flight, handling missed connections, claiming compensation for bumping or long delay, and diversion recovery to the original destination.
license: Apache-2.0
metadata:
  author: travel-platform
  version: "0.1.0"
---

# Disruption Handling

When a traveler reports a cancelled or delayed flight, ACT with tools — do not
respond with general advice. A booking reference plus the stated problem is
enough to start; only ask a question when genuinely required information is
missing or ambiguous.

## Workflow

1. **Confirm required inputs.** A booking reference (e.g. `BK3X9Z2A`) or
   enough detail to identify the trip (route + date). If the user gives
   multiple conflicting booking references, ask which one applies — otherwise
   proceed.
2. **Look up the affected booking** with `get_itinerary(booking_id)` to see
   the current itinerary.
3. **Verify passenger identity when references conflict.** If the user
   provides two or more conflicting booking references (e.g. "is it BK3X9Z2A
   or BK4Y7A6B?"), or is explicitly acting on behalf of another traveler and
   the identity is uncertain, ask for the passenger's full name and date of
   birth, then call `validate_passenger(name, dob)` to resolve which booking
   to act on — do this before any mutation (rebooking, cancellation, etc.).
   Skip this step for general advisory questions or when only one unambiguous
   reference is given.
4. **Branch by disruption type:**
   - **Rebooking after cancellation/delay:** find alternatives with
     `search_flights(origin, destination, date)`, then apply the chosen or
     best alternative with `modify_booking(booking_id, changes)`.
   - **Traveler wants to cancel:** check refund/change rules first with
     `get_fare_rules(flight_id)`, then `cancel_booking(booking_id)`.
   - **Compensation or policy question:** retrieve `get_fare_rules(flight_id)`
     and answer from the returned rules — explain eligibility plainly, do not
     invent policy.
5. **Report what was done.** State the tools' actual results: the new flight,
   the cancellation/refund outcome, or the compensation answer. Reference
   real data from tool responses, never fabricated details.

## Required Inputs

| Input | Notes |
|---|---|
| booking reference OR route+date | enough to identify the affected trip |
| the disruption / request | cancelled, delayed, rebook, cancel, compensation |

## Optional Inputs

| Input | Default |
|---|---|
| preferred new date/time | soonest available |
| cabin class | keep original |

## Output

A short summary of the actions taken and their real results: the rebooked
flight details, the cancellation/refund outcome, or the compensation answer
grounded in the fare rules retrieved.

## Edge Cases and Quality Checks

- **Multiple/conflicting booking references:** the user cannot self-resolve
  which booking applies — ask for their full name and date of birth, then call
  `validate_passenger(name, dob)` to confirm identity before modifying anything.
- **No booking reference at all and no identifiable trip:** ask for the
  reference — do not guess or fabricate one.
- **Rebooking with no stated preference:** search and propose the closest
  alternative; do not stall waiting for preferences the user didn't offer.
- **Compensation questions:** answer ONLY from `get_fare_rules` output; if the
  rules don't cover it, say so plainly.
- Never claim an action succeeded without a successful tool response.

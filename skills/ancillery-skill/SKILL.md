---
name: ancillery-skill
description: Add ancillary services to a flight booking. Use when users want to add seat selection, extra baggage, travel insurance, lounge access, priority boarding, car rental, or airport transfers after selecting or booking a flight. Also use when users ask about upgrade options, add-on costs, or what extras are available for their trip.
license: Apache-2.0
metadata:
  author: travel-platform
  version: "0.1.0"
---

# Ancillery Skill

## What are ancillary services?

Ancillary services are add-ons purchased beyond the base flight ticket. They represent a significant portion of airline and OTA revenue and are often the difference between a good and great travel experience. Common categories:

- **Seat selection** — window, aisle, extra legroom, bulkhead
- **Checked baggage** — additional bags beyond the included allowance
- **Travel insurance** — trip cancellation, medical, lost baggage coverage
- **Lounge access** — day passes for airport lounges
- **Priority boarding** — board before general passengers
- **Car rental** — at destination airport
- **Airport transfer** — pre-booked taxi or shuttle

## Workflow

1. **Identify the booking context.** Confirm the flight booking reference or selected flight this ancillary request applies to. If no booking is in context, ask the user to confirm the flight first.

2. **Identify what the user wants.** Ask which ancillary service(s) they want to add. If the user is unsure, present available categories with brief descriptions and pricing.

3. **Check eligibility and availability.** Not all ancillaries are available on all routes or fare types. Confirm what is available for this specific booking before presenting options.

4. **Present options with pricing.** For each requested service, show:
   - What is included
   - Price (per person, per leg, or flat fee — be explicit)
   - Any restrictions or conditions

5. **Confirm the user's selection.** Repeat back what they are adding and the total additional cost before adding it to the booking.

6. **Add the ancillary to the booking.** Use the approved ancillary tool. Do not fabricate pricing, availability, or confirmation codes.

7. **Confirm and summarise.** Show updated booking summary with all ancillaries added and revised total price.

## Required Inputs

| Input | Notes |
|---|---|
| Booking reference or flight | The booking this ancillary applies to |
| Ancillary type | What the user wants to add |

## Optional Inputs

| Input | Default |
|---|---|
| Seat preference | Any available if not specified |
| Insurance coverage level | Basic if not specified |
| Car rental class | Economy if not specified |

## Output

Updated booking summary including:
- All ancillaries added (type, details, price per item)
- Revised total booking cost
- Confirmation reference for each add-on where applicable

## Ancillary Pricing Reference

Present pricing clearly. Always specify:
- Whether price is **per person** or **per booking**
- Whether price applies to **each leg** or the **full round-trip**
- Currency

Example format:
> Extra checked bag: $35 per bag, per leg, per passenger

## Edge Cases and Quality Checks

- If the fare type does not allow a requested ancillary (e.g., basic economy with no seat selection), explain clearly and suggest upgrading the fare or choosing an alternative.
- Do not add ancillaries without explicit user confirmation of the price.
- If the user asks for lounge access but no lounge exists at their departure airport, say so.
- For travel insurance, do not provide medical or legal advice — describe coverage terms only and recommend reading the full policy.
- Never fabricate add-on pricing, availability, or confirmation codes.
- If the user has already included a checked bag in their base fare, clarify this before upselling additional baggage.

---
name: modify-booking
description: Modify or cancel an existing flight or hotel booking. Use when users want to change travel dates, update passenger contact details, switch cabin class, cancel a reservation, request a refund, or make any post-booking change to a confirmed reservation.
license: Apache-2.0
metadata:
  author: travel-platform
  version: "0.1.0"
---

# Modify Booking

## Workflow

1. **Identify the booking.** Ask for the booking reference (PNR or confirmation number) if not already in context. Confirm the booking details — passenger name, route, and dates — so the user can verify the correct reservation is being modified.
2. **Identify the requested change.** Determine what the user wants to change:
   - **Date or time change**: new travel date, departure time, or return date
   - **Route change**: new origin, destination, or connecting airports
   - **Cabin change**: upgrade or downgrade to a different cabin class on the same flights
   - **Passenger detail update**: name correction, contact email, or phone number
   - **Cancellation**: full trip or specific legs only
   - **Refund request**: follows a cancellation
3. **Check fare rules.** Retrieve the fare rules for the booking to determine:
   - Whether the requested change is allowed on this fare type
   - The applicable change or cancellation fee
   - Any fare difference payable for date or cabin changes
   - Refund eligibility, amount, and processing timeline for cancellations
   If fare rules cannot be retrieved, pause and inform the user before proceeding.
4. **Present the cost and consequences.** Before making any change, show the user:
   - The change or cancellation fee
   - Any fare difference (additional charge or credit)
   - The refund amount and expected processing timeline if cancelling
   - Any downstream impact — for example, ancillary services already added that may be voided by the change
5. **Get explicit confirmation.** Do not proceed with any modification until the user has confirmed they accept the cost summary.
6. **Execute the change.** Submit the modification using the approved booking tool. Do not fabricate new booking references, change confirmation codes, or refund amounts.
7. **Confirm the outcome.** Present the updated booking details or cancellation confirmation:
   - Updated or cancelled booking reference
   - New travel details (dates, cabin class) or confirmation of cancellation
   - Total additional charge or refund amount
   - Refund processing timeline where applicable

## Required Inputs

| Input | Notes |
|---|---|
| Booking reference | PNR or confirmation number |
| Change type | What the user wants to modify or cancel |

## Optional Inputs

| Input | Notes |
|---|---|
| New travel dates | Required for date changes |
| New cabin class | Required for cabin upgrades or downgrades |
| Name correction | Required for passenger name updates |
| Cancellation reason | Some fare types require a reason for refund eligibility |

## Output

A modification confirmation including:
- Updated or cancelled booking reference
- Summary of what changed (old value → new value, or "Cancelled")
- Fee charged and the payment method debited
- Refund amount and expected processing timeline (for cancellations)

## Edge Cases and Quality Checks

- Always retrieve fare rules before quoting fees — do not state change or cancellation fees from memory or inference.
- If the fare is non-changeable or non-refundable, inform the user clearly and do not attempt the modification.
- For name changes, distinguish between a minor correction (e.g., a typo) and a full name transfer — the allowed changes and fees differ.
- If the user wants to cancel only one leg of a round-trip, confirm whether this is permitted on their fare type before proceeding.
- Never proceed with a modification without explicit user confirmation of the full cost.
- Do not fabricate new confirmation numbers, change fees, or refund amounts.
- If the modification fails due to changed availability or a system error, explain the reason clearly and suggest alternatives.
- For partial cancellations on multi-passenger bookings, confirm which passengers are affected before submitting.

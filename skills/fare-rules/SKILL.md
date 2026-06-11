---
name: fare-rules
description: Look up and explain the cancellation rules, refund policy, and change fees that apply to a ticket. Use when a traveler asks a policy question — "what are the cancellation rules for my flight", "is my booking refundable", "can I change my flight date and what does it cost", "does my ticket allow a free date change without a fee", "what is the baggage allowance", "how much is it to cancel my reservation", "what is the no-show policy if I miss due to traffic". Answers whether the fare is refundable, what change fees apply, and what the baggage terms and no-show conditions allow.
license: Apache-2.0
metadata:
  author: travel-platform
  version: "0.1.0"
---

# Fare Rules

## Workflow

1. **Identify the fare in scope.** Confirm the booking reference (PNR), fare class code, or specific flight and cabin class the user is asking about. If neither is provided, ask before proceeding.
2. **Retrieve the fare rules.** Look up the fare rules using the approved tool. Do not guess or infer rules from general knowledge — retrieve them from the authoritative source for the specific booking or fare class.
3. **Parse and present the applicable rules.** For the retrieved fare, explain each of the following categories:
   - **Cancellation and refund policy**: whether the fare is refundable, the refund amount or percentage, and any deadline for cancellation to receive a full or partial refund.
   - **Change policy**: whether the fare allows date, time, or routing changes; the change fee per transaction; and whether a fare difference applies.
   - **Baggage allowance**: carry-on and checked bag counts, weight limits per bag, and overage fees.
   - **Seat selection**: whether advance seat selection is included, which seat categories are restricted (extra legroom, exit rows, bulkhead), and associated fees.
   - **Name change rules**: whether a minor name correction or full name transfer is permitted and the associated fee.
   - **Upgrade eligibility**: whether the fare can be upgraded using miles, cash, or a bid, and any blackout conditions.
4. **Summarise key restrictions up front.** Lead the response with the most important limitations. If the fare is fully non-refundable or changes incur a high fee, state this prominently before the full breakdown.
5. **State what is not covered.** If the retrieved fare rules do not address a specific topic the user asked about, say so rather than guessing.
6. **Offer next steps.** If the user wants to act on the rules — cancel, change, add baggage, or upgrade — offer to continue with the relevant skill.

## Required Inputs

| Input | Notes |
|---|---|
| Booking reference or fare class | PNR code, ticket number, or fare class code (e.g. Y, B, Q) |
| Route or flight | Required when a fare class code is provided without a booking reference |

## Optional Inputs

| Input | Default |
|---|---|
| Specific rule category | All categories returned if not specified |
| Passenger | First passenger on the booking if not specified |

## Output

A structured fare rules summary with all applicable categories:

- **Refund status**: Refundable / Partially Refundable / Non-Refundable
- **Cancellation deadline** and refund amount or percentage
- **Change fee** per transaction and fare difference rules (extra charge or credit)
- **Baggage**: carry-on allowance and checked bag allowance per leg
- **Seat selection**: included / fee-based / restricted by category
- **Name change**: correction allowed / transfer allowed / not permitted, with fee
- **Upgrade eligibility**: eligible via miles / cash / bid, or not eligible

## Edge Cases and Quality Checks

- Do not guess or generalise fare rules — retrieve them from the approved tool for the specific booking or fare class.
- If multiple passengers are on the same booking with different fare classes, confirm which rules apply to which ticket.
- Clearly distinguish between rules that apply before departure and those that apply after departure.
- Do not provide legal or financial advice. Describe what the fare rules state; recommend contacting the airline or a travel agent for complex situations.
- If fare rules data is unavailable or incomplete, say so and suggest the user contact the airline directly.
- Never fabricate penalty amounts, deadlines, or allowance quantities.

<!-- CI smoke test: verifying the eval gate pipeline runs end-to-end -->

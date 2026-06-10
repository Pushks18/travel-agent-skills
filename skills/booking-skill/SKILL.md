---
name: booking-skill
description: Purchase and confirm a brand-new flight ticket or hotel reservation. Use when the traveler says "book a flight to X for [name]", "reserve a hotel room", "book me into the Marriott", "get me a ticket to Chicago", "book the Hilton Garden Inn", "book this flight", or wants to buy and receive a booking confirmation number. Creates the reservation from scratch with passenger details and payment.
license: Apache-2.0
metadata:
  author: travel-platform
  version: "0.1.0"
---

# Booking Skill

## Workflow

1. **Identify what is being booked.** Confirm whether the user is booking a flight, hotel, or both. If a prior search was performed in this session, carry forward the selected option. Do not re-search unless the user requests it.

2. **Confirm the selected option.** If the user has already indicated which flight or hotel they want, proceed to collect passenger details without asking for reconfirmation. Only confirm if the selection is ambiguous. Never re-confirm details the user has already provided.

   For hotel bookings, the guest name and stay dates are sufficient — proceed directly through availability to 'create_booking' in the same turn.

3. **Collect passenger details.** For each passenger, collect:
   - Full legal name (as it appears on ID/passport)
   - Date of birth
   - Contact email and phone number (ask if absent, but do not block the booking on them — they can be added to the booking afterwards)
   - Passport or national ID number (flight reservations only — ask once if missing; hotels never need it)
   - Frequent flyer number (optional)

4. **Validate passenger information.** Check that names contain no special characters that would be rejected and dates of birth are plausible. Flag any issues before attempting to book. Missing contact details are a follow-up item, not a blocker: proceed with the booking using the details provided and note what is still needed.

5. **Check availability.** Confirm the selected flight or hotel is still available at the quoted price. If it is no longer available, inform the user immediately and offer to re-search.

6. **Create the booking.** Submit the booking using the approved booking tool. Do not fabricate confirmation numbers, PNR codes, or booking IDs.

7. **Confirm the booking.** Present the confirmed booking details:
   - Booking reference / PNR
   - Passenger name(s)
   - Flight or hotel details
   - Total price charged
   - Cancellation and change policy summary

8. **Offer next steps.** Ask if the user needs ancillary services (seat selection, baggage, insurance), wants to add a hotel, or needs the itinerary sent.

## Required Inputs

| Input | Notes |
|---|---|
| Flight or hotel selection | From a prior search or explicitly stated by the user |
| Passenger full name | Legal name matching travel document |
| Date of birth | Required for all passengers |
| Contact email | For booking confirmation — ask if absent, but proceed without it |
| Contact phone | For disruption notifications — ask if absent, but proceed without it |

## Optional Inputs

| Input | Default |
|---|---|
| Passport / ID number | Required for international; optional for domestic |
| Frequent flyer number | No loyalty points applied if omitted |
| Seat preference | Assigned automatically if not specified |

## Output

Confirmed booking summary including:
- Booking reference / PNR
- Passenger(s) name and details
- Flight: number, route, date, departure time, cabin class
- Total price and currency
- Cancellation policy (free cancellation window, fees after)

## Edge Cases and Quality Checks

- If availability has changed since the search, do not proceed — inform the user and offer alternatives.
- If passenger name contains characters that are not accepted (special characters, excessive length), ask the user to re-enter.
- Do not proceed with a booking if required passenger fields are missing.
- Never fabricate booking reference numbers, PNR codes, or ticket numbers.
- For multi-passenger bookings, collect and validate details for every passenger before submitting.
- If the booking fails, explain the reason clearly and suggest re-trying or contacting support.
- For round-trips, confirm both legs are included in a single booking where possible.

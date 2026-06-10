---
name: planning-skill
description: Build a complete multi-day travel itinerary spanning flights, accommodation, and activities. Use when a traveler says "plan a trip to X", "create an itinerary for Y days", "I want to visit Z for a week", or asks for a day-by-day outline covering multiple components across several days. Best for open-ended trip design when no single booking or search has been identified yet.
license: Apache-2.0
metadata:
  author: travel-platform
  version: "0.1.0"
---

# Planning Skill

## Workflow

1. **Clarify trip parameters.** Before planning, confirm:
   - Destination (city, region, or country)
   - Travel dates or trip duration
   - Origin city (for flight search)
   - Number of travellers (ensure inclusion in all flight and hotel search toolcalls)
   - Trip purpose (leisure, business, family, honeymoon, etc.)
   - Budget range (optional but helpful)
   - Any hard requirements (direct flights only, specific hotel area, accessibility needs)

   Adhere strictly to the user-specified trip duration: flight dates, hotel check-in/check-out dates, and the daily outline must all align with that duration, and the same travel dates must be used consistently across all tool calls.

   Once trip parameters are clarified, proceed directly to executing tool calls for flight searches (using 'search_flights'), hotel searches (using 'search_hotels'), and eventually 'create_booking' if the user wishes to finalize plans.

2. **Build the flight component with the 'search_flights' tool.** Use the tool to search for flights matching the confirmed parameters. Present the top 2-3 options with key trade-offs (price vs. duration vs. stops). Ask the user to confirm a preferred flight before proceeding.

3. **Build the accommodation component with the 'search_hotels' tool.** Use the tool to search for hotels near the user's preferred area (city centre, near venue, near airport). Present 2-3 options covering different price points. Note star rating, location, and included amenities.

   If the travel request spans multiple cities with specific transitions (e.g. Sydney to Brisbane to Melbourne), call 'search_flights' or 'search_hotels' for each segment in the indicated order and timing, then consolidate the segments into one itinerary.

4. **Suggest a daily activity outline.** Based on trip duration and purpose, suggest a lightweight day-by-day outline:
   - Day 1: Arrival, check-in, nearby dinner
   - Day 2+: Key attractions, experiences, or meetings relevant to the purpose
   - Last day: Checkout, airport transfer, departure buffer

   Keep suggestions brief. Do not fabricate specific restaurant names, ticket prices, or opening hours — state assumptions clearly.

5. **Summarise the full itinerary.** Present the complete plan in a structured format:
   - Flights (outbound and return)
   - Hotel (name, dates, nightly rate, total)
   - Daily outline
   - Estimated total trip cost (flights + hotel; note activities are estimates)

6. **Offer to proceed.** Ask which components the user wants to book first, or whether they want to adjust anything before booking.

   When all components are confirmed, use the 'create_booking' tool to finalize any bookings the user has requested during the session.

## Required Inputs

| Input | Notes |
|---|---|
| Destination | City, region, or country |
| Travel dates or duration | Specific dates preferred; duration acceptable |
| Origin | For flight search |
| Traveller count | Defaults to 1 adult |

## Optional Inputs

| Input | Default |
|---|---|
| Trip purpose | Leisure assumed if not stated |
| Budget range | No restriction |
| Accommodation area preference | City centre |
| Flight preference | Cheapest available |

## Output

A structured trip plan containing:
- **Flights**: options with price, duration, stops
- **Hotel**: options with location, rating, price per night
- **Daily outline**: lightweight day-by-day suggestions
- **Estimated total cost**: flights + hotel (activities noted separately as estimates)

## Edge Cases and Quality Checks

- If the destination is vague (e.g. "somewhere warm"), ask the user to choose between 2-3 suggested destinations rather than guessing.
- If travel dates are flexible or relative ("next month", "any weekend in May"), pick a reasonable concrete date within the stated range, state the assumption clearly, and search — do not block the search waiting for date confirmation.
- Do not fabricate specific restaurant names, attraction ticket prices, or local transport schedules — state that these are suggestions to research.
- For business trips, prioritise hotels near the meeting venue and direct flights where possible.
- For family trips, flag child-friendly accommodation and activities.
- If the budget is very low for the destination and dates, briefly note the constraint, then still run 'search_flights' and 'search_hotels' to ground the answer in what is actually available — report the cheapest real options even if they exceed the stated budget.
- Keep the daily outline lightweight — this is a starting framework, not a minute-by-minute schedule.
- Always note that hotel and flight prices are subject to change and should be confirmed at time of booking.
- Always include the number of passengers for flights and the number of guests for hotels in tool calls. Confirm these numbers if they are not explicitly stated by the user.
- An itinerary build request is not satisfied by a text-only response: call 'search_flights' and 'search_hotels' with all required parameters (origin, destination, date, and passenger count for flights; location, check-in, check-out, and guest count for hotels), and use 'create_booking' only when the user has requested or confirmed a booking.
- When adding extra services to a booking (e.g. a car rental), fill in all parameters of the 'add_ancillary' tool call, including the service details describing what is being added.

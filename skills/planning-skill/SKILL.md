---
name: planning-skill
description: Plan a complete multi-component trip itinerary. Use when users want to plan a full trip — not just a single flight or hotel — including suggestions for flights, accommodation, activities, and logistics. Use when users say "plan a trip to X", "I want to visit Y for Z days", or ask for an end-to-end travel plan with multiple components.
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
   - Number of travellers
   - Trip purpose (leisure, business, family, honeymoon, etc.)
   - Budget range (optional but helpful)
   - Any hard requirements (direct flights only, specific hotel area, accessibility needs)

2. **Build the flight component.** Search for flights matching the confirmed parameters. Present the top 2-3 options with key trade-offs (price vs. duration vs. stops). Ask the user to confirm a preferred flight before proceeding.

3. **Build the accommodation component.** Search for hotels near the user's preferred area (city centre, near venue, near airport). Present 2-3 options covering different price points. Note star rating, location, and included amenities.

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
- If travel dates are relative ("next month", "in summer"), confirm exact dates before searching.
- Do not fabricate specific restaurant names, attraction ticket prices, or local transport schedules — state that these are suggestions to research.
- For business trips, prioritise hotels near the meeting venue and direct flights where possible.
- For family trips, flag child-friendly accommodation and activities.
- If the budget is very low for the destination and dates, say so clearly rather than presenting options that exceed it.
- Keep the daily outline lightweight — this is a starting framework, not a minute-by-minute schedule.
- Always note that hotel and flight prices are subject to change and should be confirmed at time of booking.

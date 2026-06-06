---
name: flight-search
description: Find and compare available flights between two cities. Use when a traveler says "find flights from X to Y", "search for flights", "what flights go from SFO to JFK", "I need a roundtrip to Seattle", "show me airfare", "are there budget flights to Z", "I want to fly to Denver on this date", or "I need a business class seat to London". Covers browsing routes, schedules, prices, stops, cabin class availability, and airline options.
license: Apache-2.0
metadata:
  author: travel-platform
  version: "0.1.0"
---

# Flight Search

## Workflow

1. **Check required inputs.** If origin, destination, or departure date are present in the request, proceed immediately to search. Only ask for missing fields if they are genuinely absent — do not ask to reconfirm information the user has already provided.
2. **Identify trip type.** Determine if the request is one-way, round-trip, or multi-city. Apply the appropriate search logic for each leg.
3. **Search for flights.** Query available flight data using the user's confirmed inputs. Search all relevant cabin classes unless the user has specified one.
4. **Filter results.** Apply any user preferences: number of stops, preferred airlines, departure time windows, maximum layover duration, or baggage requirements.
5. **Rank results.** Sort by the user's stated priority — price, duration, fewest stops, or a balanced score. Default to price-ascending when no priority is stated.
6. **Format the response.** Present results using the standard flight result format. See [result format reference](references/result-format.md).
7. **Highlight trade-offs.** Call out key differences between top options — for example, a cheaper fare with a long layover versus a direct flight at a higher price.
8. **State limitations.** If data is incomplete, prices may have changed, or the search could not cover all airlines, say so clearly.

## Required Inputs

| Input | Notes |
|---|---|
| Origin | IATA airport code or city name |
| Destination | IATA airport code or city name |
| Departure date | ISO 8601 date (YYYY-MM-DD) |
| Return date | Required for round-trip; omit for one-way |
| Passenger count | Defaults to 1 adult if not specified |

## Optional Inputs

| Input | Default |
|---|---|
| Cabin class | Economy |
| Max stops | No restriction |
| Preferred airlines | No restriction |
| Max price | No restriction |
| Baggage requirements | No restriction |
| Departure time window | No restriction |

## Output

Present results using the standard format described in [references/result-format.md](references/result-format.md).

Each result must include at minimum:
- Flight number(s) and operating airline(s)
- Departure and arrival times with timezone
- Total duration and number of stops
- Cabin class
- Price per person and total price
- Baggage policy summary

## Edge Cases and Quality Checks

- If origin and destination resolve to the same airport, ask the user to clarify.
- If no results are found, tell the user and suggest relaxing one filter at a time (dates, stops, or price).
- If the user requests a cabin class that is unavailable on a route, note this and show the next available class.
- Do not fabricate prices, flight numbers, schedules, or airline policies.
- Do not present results from data sources that are outside the approved tool set.
- For multi-city trips, treat each leg independently and present results grouped by leg.

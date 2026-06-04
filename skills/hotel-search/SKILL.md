---
name: hotel-search
description: Search, compare, and summarise hotel options. Use when users ask for hotel availability, accommodation options, room types, hotel ratings, amenity comparisons, location guidance, or price-aware hotel recommendations for a destination.
license: Apache-2.0
metadata:
  author: travel-platform
  version: "0.1.0"
---

# Hotel Search

## Workflow

1. **Confirm required inputs.** Ask for any missing required fields before searching. Do not guess destination, check-in or check-out dates, or guest count.
2. **Identify accommodation preferences.** Determine whether the user has stated a preferred area, property type (hotel, apartment, hostel, resort), star rating, or specific amenities. Note any hard requirements such as wheelchair accessibility, pet-friendly policy, pool, or gym.
3. **Search for hotels.** Query available accommodation options using the confirmed inputs. Include a range of price points unless the user has specified a budget ceiling.
4. **Filter results.** Apply user-stated preferences: location, star rating, amenities, price range, cancellation policy, or breakfast inclusion.
5. **Rank results.** Sort by the user's stated priority — price, rating, proximity to a landmark, or a balanced score. Default to price-ascending when no priority is stated.
6. **Format the response.** Present results in a structured block. Each result must include:
   - Property name and star rating
   - Location: district and distance from city centre or stated landmark
   - Room type available at the quoted price
   - Price per night and total price for the stay, with currency
   - Key included amenities (WiFi, breakfast, parking, pool)
   - Cancellation policy: free cancellation deadline and fee after that date
7. **Highlight trade-offs.** Call out key differences between top options — for example, a central hotel at a higher price versus a suburban property with free parking at a lower price.
8. **State limitations.** If data is incomplete, prices may have changed, or availability could not be confirmed, say so clearly.

## Required Inputs

| Input | Notes |
|---|---|
| Destination | City, district, or landmark |
| Check-in date | ISO 8601 date (YYYY-MM-DD) |
| Check-out date | ISO 8601 date (YYYY-MM-DD) |
| Guest count | Defaults to 1 adult if not specified |

## Optional Inputs

| Input | Default |
|---|---|
| Property type | Any |
| Star rating | No restriction |
| Max price per night | No restriction |
| Preferred area | City centre |
| Required amenities | No restriction |
| Cancellation policy | Any |
| Breakfast included | Not required |
| Number of rooms | 1 |

## Output

Present a ranked list of options. Each result must include at minimum:
- Property name and star rating
- Location with distance from city centre or stated reference point
- Room type available at quoted price
- Price per night and total price for the stay
- Included amenities
- Cancellation policy with free cancellation deadline

## Edge Cases and Quality Checks

- If check-in and check-out dates are the same or check-out is before check-in, ask the user to clarify.
- If no results match the given inputs, suggest relaxing one filter at a time (dates, area, star rating, or budget).
- If the requested property type is unavailable in the destination, say so and offer the closest alternative.
- Do not fabricate hotel names, room prices, availability, or amenity details.
- Do not present results from data sources outside the approved tool set.
- For group bookings (more than 5 rooms), note that group rates may be available and recommend contacting the property directly.
- Always note that displayed prices are subject to availability and may change between search and booking.

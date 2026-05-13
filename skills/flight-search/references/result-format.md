# Flight Search Result Format

Each flight option must be presented as a structured block. Use this format consistently so consuming agents and downstream projects can parse results reliably.

---

## Single Result Block

```
Flight:        <airline> <flight_number> [+ <airline> <flight_number> ...]
Route:         <origin_code> → <destination_code>
Departure:     <YYYY-MM-DD HH:MM timezone>
Arrival:       <YYYY-MM-DD HH:MM timezone>
Duration:      <Xh YYm>
Stops:         <nonstop | 1 stop (<layover_airport>, <layover_duration>) | N stops>
Cabin:         <Economy | Premium Economy | Business | First>
Price:         <currency symbol><amount> per person (<currency symbol><total> total for <n> passenger(s))
Baggage:       <carry-on: yes/no | checked: X bags included | fees apply>
```

---

## Field Definitions

| Field | Format | Notes |
|---|---|---|
| `airline` | Airline name or IATA carrier code | Use full name on first reference, code thereafter |
| `flight_number` | Carrier code + number, e.g. `AA 101` | Include all flight numbers for connecting flights |
| `origin_code` | IATA airport code | e.g. `JFK`, `LHR` |
| `destination_code` | IATA airport code | e.g. `CDG`, `SIN` |
| `departure` | `YYYY-MM-DD HH:MM TZ` | Use local time at origin with timezone label |
| `arrival` | `YYYY-MM-DD HH:MM TZ` | Use local time at destination with timezone label |
| `duration` | `Xh YYm` | Total elapsed travel time including layovers |
| `stops` | Text description | Name the layover airport and duration for 1-stop; list all for multi-stop |
| `cabin` | One of the four standard values | Match exactly; do not abbreviate |
| `price` | Symbol + amount, e.g. `$342` | Always show per-person and total |
| `baggage` | Short text summary | State whether carry-on and checked bags are included or fee-based |

---

## Multi-Result Summary Block

When presenting multiple options, lead with a ranked summary table before showing individual blocks:

```
# Flight Options: <origin_code> → <destination_code> on <departure_date>

| # | Airline       | Departure | Arrival | Duration | Stops    | Cabin   | Price/person |
|---|---------------|-----------|---------|----------|----------|---------|-------------|
| 1 | Delta DL 402  | 08:00 EST | 14:35 GMT| 7h 35m  | Nonstop  | Economy | $489        |
| 2 | AA 101+BA 178 | 06:15 EST | 15:20 GMT| 9h 05m  | 1 (LHR)  | Economy | $312        |
| 3 | United UA 22  | 11:00 EST | 23:55 GMT| 12h 55m | 1 (ORD)  | Economy | $278        |
```

Follow the summary table with full result blocks for the top 3 options, or all options if 3 or fewer were found.

---

## Round-Trip Format

For round-trip searches, present outbound and return legs in separate sections:

```
## Outbound: <origin_code> → <destination_code>, <departure_date>
<summary table and result blocks for outbound leg>

## Return: <destination_code> → <origin_code>, <return_date>
<summary table and result blocks for return leg>

## Combined Price

| Outbound option | Return option | Total price |
|---|---|---|
| Option 1 | Option 1 | $978 |
| Option 1 | Option 2 | $801 |
| Option 2 | Option 1 | $801 |
```

---

## Example Output

**Search:** JFK → LHR, 2025-06-15, 1 adult, Economy

```
# Flight Options: JFK → LHR on 2025-06-15

| # | Airline         | Departure      | Arrival        | Duration | Stops   | Cabin   | Price/person |
|---|-----------------|----------------|----------------|----------|---------|---------|-------------|
| 1 | British BA 178  | 21:00 EST      | 09:05+1 GMT    | 7h 05m   | Nonstop | Economy | $620        |
| 2 | Delta DL 1+VS 3 | 18:30 EST      | 10:15+1 GMT    | 8h 45m   | 1 (ATL) | Economy | $430        |
| 3 | Iberia IB 6253  | 19:45 EST      | 12:30+1 GMT    | 9h 45m   | 1 (MAD) | Economy | $395        |

---

Flight:     British Airways BA 178
Route:      JFK → LHR
Departure:  2025-06-15 21:00 EST
Arrival:    2025-06-16 09:05 GMT
Duration:   7h 05m
Stops:      Nonstop
Cabin:      Economy
Price:      $620 per person ($620 total for 1 passenger)
Baggage:    Carry-on included | Checked bags: fees apply

---

Flight:     Delta DL 1 + Virgin Atlantic VS 3
Route:      JFK → ATL → LHR
Departure:  2025-06-15 18:30 EST
Arrival:    2025-06-16 10:15 GMT
Duration:   8h 45m
Stops:      1 stop (ATL, 55m layover)
Cabin:      Economy
Price:      $430 per person ($430 total for 1 passenger)
Baggage:    Carry-on included | 1 checked bag included
```

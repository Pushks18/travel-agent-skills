---
name: gate-terminal-change
description: Detect gate or terminal changes and calculate the cascading effect on boarding, connections, baggage, ground transport, hotels, and meetings. Use when a flight's gate or terminal is reassigned and you need to assess missed-boarding risk and downstream itinerary impact.
license: Apache-2.0
metadata:
  version: "0.1.0"
  author: travel-platform
  category: disruption-detection
---

# Gate / Terminal Change Skill

Detect a gate or terminal change and calculate how it cascades through the rest of the trip chain. A gate change is rarely isolated: if it threatens boarding, it threatens every downstream event that depends on this flight.

## When to Use
- A flight's gate or terminal is reassigned
- Need to assess whether the traveler can still reach the new gate before boarding closes
- Need to evaluate downstream impact on connections, baggage, transport, hotels, or meetings

## Workflow

### Step 1: Parse Input
Extract the flight number, old/new gate or terminal, current traveler location, the timing fields (current/boarding-start/boarding-close/departure), and the Trip ID and User ID from `[Context: ...]`. See the full input shape in [references/schema.md](references/schema.md#input-schema).

### Step 2: Get Trip Data
Call `get_trip_bookings(trip_id)` to retrieve:
- **Flights**: This segment, connections, layover buffers
- **Hotels**: Name, check-in date/time, location
- **Cars/Cabs**: Pickup/drop-off times
- **Activities/Meetings**: Scheduled times
- **Traveler**: Age, mobility, medical conditions, party size

### Step 3: Gather Cascading Effect Inputs
For a gate/terminal change, the agent should check:
- Current traveler location
- New gate/terminal **walking ETA**
- Boarding **start** / boarding **close** time
- Flight **departure** time
- **Connection** flight, if any
- **Baggage / security / immigration** dependency
- **Ground transport / hotel / meeting** dependency after arrival

### Step 4: Apply the Cascading Risk Formula

```
Available Time  = Boarding Close Time − Current Time
Movement Buffer = Available Time − Walking ETA
Cascading Risk  = Impact on next trip event
```

A negative or near-zero Movement Buffer means the traveler may miss boarding, which propagates risk to every downstream event.

### Step 5: Determine Severity

| Condition | Signal to PA |
|-----------|--------------|
| Traveler can reach new gate with **> 15 min** buffer | LOW |
| Traveler can reach gate, but buffer is **5–15 min** | MEDIUM |
| Walking ETA **exceeds** available time, **terminal change** required, or **connection risk** created | HIGH |

Escalate severity for traveler vulnerability:
- Age 70+ (+1 level)
- Wheelchair / mobility assistance (+1 level)
- Medical conditions (+1 level)
- Large party 5+ (+1 level)

### Step 6: Add Downstream Impact
After detecting the gate/terminal change, check:

```
If flight departure delay or missed boarding risk:
    Check connection flight
    Check layover buffer
    Check arrival transport
    Check hotel check-in / meeting time
    Calculate downstream impact
```

**Cascading Effect Check** (applies after ANY trip-critical disruption): evaluate whether the event impacts downstream itinerary items such as boarding, connections, baggage, airport transfer, hotel check-in, or meetings. Fire a signal to PA as LOW, MEDIUM, or HIGH based on buffer loss and missed-event probability.

### Step 7: Generate Report

```
GATE/TERMINAL CHANGE - Flight {flight_number}

SUMMARY:
Flight {flight} gate changed {old_gate} → {new_gate} ({old_terminal} → {new_terminal}).
Severity: {LOW | MEDIUM | HIGH}
Cascading Effect: {true | false}

TIMING:
Current time:    {current_time}
Boarding closes: {boarding_close}
Walking ETA:     {walking_eta} min
Available time:  {available_time} min
Movement buffer: {movement_buffer} min

DOWNSTREAM IMPACT:
- Connection: {flight} - {status}
- Baggage/Security/Immigration: {impact}
- Ground transport: {impact}
- Hotel/Meeting: {impact}

RECOMMENDED ACTION:
{action}
```

### Step 8: Send Notification

```python
send_pa_notification(
    title="Gate/Terminal Change - {severity}",
    message="Flight {number} moved to {new_gate}. Walking ETA {eta} min, buffer {buffer} min. {downstream_summary}",
    user_id="{user_id}",
    severity="{LOW | MEDIUM | HIGH}",
    notification_type="disruption_alert"
)
```

## Analysis Considerations
- **Terminal changes**: Add 30–45 min for terminal transfers (trains, shuttles, re-screening)
- **Security re-screening**: A terminal change may require passing security again
- **Walking ETA**: Account for distance, crowds, and traveler mobility
- **Baggage / immigration**: Factor dependencies that consume buffer time
- **Connections**: A missed boarding cascades to connection, transport, hotel, and meetings
- **Timezones**: Boarding/departure times may differ from downstream local times

## Output Schema

Emit an object carrying the `event`, flight and gate fields, `severity` (`HIGH | MEDIUM | LOW`), `cascading_effect`, the `timing` block (current/boarding-close times, walking ETA, available time, movement buffer), per-item `downstream_impact`, `reason`, and `recommended_action`. See the full field shape in [references/schema.md](references/schema.md#output-schema).

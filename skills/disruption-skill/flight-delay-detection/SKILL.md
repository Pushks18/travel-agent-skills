---
name: flight-delay-detection
description: Detect potential disruptions caused by flight delays and analyze cascading impacts on connections, hotels, ground transport, and activities.
license: Apache-2.0
metadata:
  version: "0.1.0"
  author: travel-platform
  category: disruption-detection
---

# Flight Delay Detection Skill

Analyze flight delays to detect ALL potential disruptions across the entire trip.

## When to Use
- Flight departure or arrival is delayed
- Need to analyze downstream impacts on hotels, cars, connections

## Workflow

### Step 1: Parse Input
Extract from input:
- Flight number and delay duration
- Trip ID from `[Context: Trip ID: ...]`
- User ID from `[Context: User ID: ...]`

### Step 2: Get Trip Data
Call `get_trip_bookings(trip_id)` to retrieve:
- **Flights**: Segments, arrival times, connections
- **Hotels**: Name, check-in date/time, location
- **Cars/Cabs**: Pickup/drop-off times
- **Activities**: Scheduled times
- **Traveler**: Age, mobility, medical conditions

### Step 3: Analyze Impact on ALL Bookings

#### Connection Analysis
- Calculate time gap between delayed arrival and next departure
- Consider terminal changes, airport size
- Account for traveler mobility needs
- Flag if connection becomes tight or missed

#### Hotel Impact (CRITICAL)
- Compare new flight arrival time with hotel check-in date
- Check if same-day check-in is at risk
- Verify flight destination matches hotel location
- Flag late arrivals that need hotel notification

#### Car/Cab Impact (CRITICAL)
- Compare new flight arrival with scheduled pickup time
- Flag if pickup is now BEFORE flight lands (invalid)
- Check if buffer time is insufficient (< 30 min)

#### Activity Impact
- Compare arrival + travel time with activity start
- Flag if activity will be missed or delayed

#### Traveler Vulnerability
Consider escalating severity for:
- Age 70+ (+1 level)
- Wheelchair/mobility assistance (+1 level)
- Medical conditions (+1 level)
- Large party 5+ (+1 level)

### Step 4: Generate Report

```
DISRUPTION ANALYSIS - Flight {flight_number} Delay

SUMMARY:
Flight {flight} ({route}) delayed {minutes} minutes.
Risk Level: {L0-L5}
Effect Type: LOCALIZED | CASCADING

AFFECTED BOOKINGS:
- Flight: {connection} - {status}
- Hotel: {hotel_name} - {impact}
- Car: {pickup_details} - {impact}

DISRUPTIONS DETECTED:
1. {TYPE} ({SEVERITY})
   Details: {explanation with times}
   Affected: {booking}
   Action: {recommendation}

CASCADING IMPACT CHAIN:
{delay} → {arrival change} → {connection impact} → {hotel impact} → {car impact}

RECOMMENDED ACTIONS:
1. {priority}: {action}
```

### Step 5: Send Notification

```python
send_pa_notification(
    title="Flight Disruption - {severity}",
    message="Flight {number} delayed {duration}. AFFECTED: Hotel ({name} - {impact}), Car ({impact}). Actions: {list}",
    user_id="{user_id}",
    severity="{L0-L5}",
    notification_type="disruption_alert"
)
```

## Disruption Types

### Connection-Related
| Type | Severity | Condition |
|------|----------|-----------|
| `missed_connection` | CRITICAL | Connection clearly not viable |
| `tight_connection` | HIGH | Connection at significant risk |
| `potentially_tight_connection` | MEDIUM | Connection borderline feasible |

### Hotel-Related
| Type | Severity | Condition |
|------|----------|-----------|
| `hotel_checkin_risk` | HIGH | Arrival significantly after deadline |
| `late_hotel_arrival` | MEDIUM | Late but likely manageable |
| `hotel_notification_needed` | LOW | Should notify hotel |

### Ground Transport
| Type | Severity | Condition |
|------|----------|-----------|
| `cab_timing_mismatch` | HIGH | Pickup before flight lands |
| `cab_buffer_tight` | MEDIUM | < 30min between landing and pickup |
| `transfer_rescheduling_needed` | MEDIUM | Pre-paid transfer timing off |

### Activities
| Type | Severity | Condition |
|------|----------|-----------|
| `activity_missed` | HIGH | Will miss activity start |
| `activity_delayed_start` | MEDIUM | Tight timing for activity |

## Risk Levels

| Level | Classification | Action |
|-------|----------------|--------|
| L0 | No impact | Informational only |
| L1 | Minor inconvenience | No action needed |
| L2 | Moderate issue | Monitoring recommended |
| L3 | Significant problem | Action recommended |
| L4 | Critical impact | Urgent action required |
| L5 | Trip failure | Immediate escalation |

## Analysis Considerations

- **Timezones**: Flight times often UTC, hotels/cabs use local time
- **Terminal changes**: Add 30-45 min for terminal transfers
- **International**: Add 30-60 min for immigration/customs
- **Baggage claim**: Factor 20-30 min for bags
- **Pre-paid services**: Note cancellation fee implications

## Output Schema

```json
{
  "disruption_id": "DISR_001",
  "type": "hotel_checkin_risk",
  "severity": "HIGH",
  "risk_level": "L3",
  "affected_bookings": ["HTL_12345"],
  "description": "Flight arrives 20:30, hotel check-in deadline 18:00",
  "details": {
    "hotel_name": "Hilton LAX",
    "check_in_date": "2026-05-24",
    "check_in_time": "15:00",
    "new_arrival": "20:30",
    "impact": "Late arrival - may need to confirm reservation"
  },
  "recommended_actions": [
    "Notify hotel of late arrival",
    "Confirm reservation is held"
  ]
}
```

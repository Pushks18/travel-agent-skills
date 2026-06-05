# Gate / Terminal Change — Input & Output Schemas

Load this file when you need the exact field shapes for input parsing or the PA notification payload. The workflow, cascading-risk formula, and severity logic live in `SKILL.md`; this file is only the data contracts.

## Input schema

Collect or infer any available subset. Mark missing fields as unknown rather than guessing.

```json
{
  "trip_id": "string",
  "user_id": "string",
  "flight_number": "string",
  "old_gate": "string",
  "new_gate": "string",
  "old_terminal": "string | null",
  "new_terminal": "string | null",
  "current_location": "string",
  "current_time": "datetime",
  "boarding_start": "datetime",
  "boarding_close": "datetime",
  "departure_time": "datetime",
  "walking_eta_min": "integer",
  "dependencies": {
    "connection": "string | null",
    "baggage_security_immigration": "string | null",
    "ground_transport_hotel_meeting": "string | null"
  }
}
```

## Output schema

```json
{
  "event": "Gate/Terminal Change",
  "flight_number": "AA123",
  "old_gate": "B12",
  "new_gate": "C45",
  "severity": "HIGH | MEDIUM | LOW",
  "cascading_effect": true,
  "timing": {
    "current_time": "15:10",
    "boarding_close": "15:35",
    "walking_eta_min": 22,
    "available_time_min": 25,
    "movement_buffer_min": 3
  },
  "downstream_impact": {
    "connection": "at_risk | monitor | no_impact",
    "ground_transport": "at_risk | monitor | no_impact",
    "hotel_or_meeting": "at_risk | monitor | no_impact"
  },
  "reason": "New gate requires 22 minutes walking time with only 3 minutes buffer before boarding closes.",
  "recommended_action": "Notify traveler immediately, reroute from current location, and monitor missed-boarding risk."
}
```

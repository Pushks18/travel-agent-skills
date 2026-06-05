# Flight Risk Detection — Input & Output Schemas

Load this file when you need the exact field shapes for input parsing or the PA-facing flight-risk cascade report. The behavioral rules, severity model, and reasoning logic live in `SKILL.md`; this file is only the data contracts.

## Input schema

Collect or infer any available subset. Mark missing fields as unknown rather than guessing.

```json
{
  "traveler_id": "string",
  "trip_id": "string",
  "flight": {
    "pnr": "string",
    "airline": "string",
    "flight_number": "string",
    "departure_airport": "string",
    "arrival_airport": "string",
    "connection_airport": "string | null",
    "scheduled_departure": "datetime",
    "scheduled_arrival": "datetime"
  },
  "risk_signal": {
    "category": "weather | airport_conditions | airspace_atc | airline_operations | inbound_aircraft | crew_or_maintenance | strike_labor | security_event | natural_event | other",
    "description": "string",
    "source": "weather_service | airport_ops | atc | airline | gds | news | provider_ops | manual",
    "confidence": "confirmed | probable | unverified",
    "delay_likelihood": "string | null",
    "expected_impact": "delay | cancellation | diversion | unknown",
    "time_window": {
      "starts": "datetime | null",
      "ends": "datetime | null"
    }
  },
  "itinerary": {
    "connections": [],
    "hotels": [],
    "ground_transport": [],
    "activities": [],
    "meetings": []
  },
  "traveler_context": {
    "current_location": "string | null",
    "accessibility": "string | null",
    "medical": "string | null",
    "party_size": "integer | null",
    "priority": "string | null"
  }
}
```

## Output schema — PA Flight Risk Cascade Report

Compact JSON shape for system-facing PA outputs. This is a report-and-advise payload: it carries reasoning, severity, the full cascade, and advisory next steps, but no major action is taken. By default `pa_payload_type` is `CASCADING_REPORT_ONLY`, `severity` is one of `HIGH | MEDIUM | LOW`, and `specific_recommendations_included` is `false`.

```json
{
  "skill": "Flight Risk Detection",
  "risk_category": "weather | airport_conditions | airspace_atc | airline_operations | inbound_aircraft | crew_or_maintenance | strike_labor | security_event | natural_event | other",
  "expected_impact": "delay | cancellation | diversion | unknown",
  "severity": "LOW | MEDIUM | HIGH | CRITICAL",
  "pa_payload_type": "CASCADING_REPORT_ONLY",
  "confidence": "confirmed | probable | unverified",
  "reasoning": "why this severity, and how the flight risk cascades across the trip",
  "risk_summary": {
    "flight": "",
    "what": "",
    "when": "",
    "source": ""
  },
  "cascade_summary": {
    "connection": "",
    "hotel": "",
    "ground_transport": "",
    "activities": "",
    "meetings": "",
    "traveler_impact": ""
  },
  "recommended_next_steps": [
    "advisory action for the PA to direct the traveler — not executed"
  ],
  "monitoring_status": "ACTIVE | NOT_REQUIRED | UNKNOWN",
  "pa_guidance": "",
  "action_center_status": "",
  "requires_traveler_confirmation": true,
  "major_action_taken": false,
  "specific_recommendations_included": false
}
```

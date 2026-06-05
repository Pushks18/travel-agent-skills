# Flight Disruption Detection — Input & Output Schemas

Load this file when you need the exact field shapes for input parsing or the PA-facing cascade report. The behavioral rules, severity model, and handler logic live in `SKILL.md`; this file is only the data contracts.

## Input schema

Collect or infer any available subset. Mark missing fields as unknown rather than guessing.

```json
{
  "traveler_id": "string",
  "trip_id": "string",
  "use_case_id": "UC-066 | UC-068",
  "disruption_type": "FLIGHT_CANCEL | AIRPORT_SHUTDOWN",
  "source": "airline | airport_ops | atc | gds | travel_provider | manual_ops",
  "confidence": "confirmed | probable | unverified",
  "affected_segment": {
    "flight": "string",
    "departure_airport": "string",
    "arrival_airport": "string",
    "connection_airport": "string | null",
    "scheduled_departure": "datetime",
    "scheduled_arrival": "datetime"
  },
  "traveler_current_location": "string | null",
  "itinerary_dependencies": {
    "connection": [],
    "hotel": [],
    "car_rental": [],
    "transfer": [],
    "activities": [],
    "meetings": []
  },
  "constraints": {
    "airline_preference": "string",
    "cabin": "string",
    "budget": "string",
    "refund_eligibility": "string",
    "accessibility": "string",
    "visa_immigration": "string",
    "baggage": "string",
    "loyalty": "string",
    "traveler_priority": "string"
  }
}
```

## Output schema — PA Cascade Report

Compact JSON shape for system-facing PA outputs. This is a report-and-advise payload: it carries reasoning, severity, the full cascade, and advisory next steps, but no major action is taken. By default `pa_payload_type` is `CASCADING_REPORT_ONLY`, `severity` is one of `HIGH | MEDIUM | LOW`, and `specific_recommendations_included` is `false`.

```json
{
  "use_case_id": "UC-066 | UC-068",
  "skill": "Flight Disruption Orchestrator",
  "event_type": "FLIGHT_CANCEL | AIRPORT_SHUTDOWN",
  "severity": "LOW | MEDIUM | HIGH | CRITICAL",
  "pa_payload_type": "CASCADING_REPORT_ONLY",
  "reasoning": "why this severity, and how the disruption cascades across the trip",
  "affected_segment": {
    "flight": "",
    "origin": "",
    "destination": "",
    "scheduled_departure": "",
    "scheduled_arrival": ""
  },
  "cascade_summary": {
    "connection": "",
    "hotel": "",
    "car_rental": "",
    "transfer": "",
    "activities": "",
    "meetings": ""
  },
  "recommended_next_steps": [
    "advisory action for the PA to direct the traveler — not executed"
  ],
  "recovery_options_status": "AVAILABLE_FOR_REVIEW | NOT_REQUIRED | UNKNOWN",
  "pa_guidance": "",
  "action_center_status": "",
  "requires_traveler_confirmation": true,
  "major_action_taken": false,
  "specific_recommendations_included": false
}
```

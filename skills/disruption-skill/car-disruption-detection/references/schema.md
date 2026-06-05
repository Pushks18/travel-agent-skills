# Car Disruption Detection — Input & Output Schemas

Load this file when you need the exact field shapes for input parsing or the PA-facing cascade report. The operating principle, trigger conditions, severity model, cascade logic, and guardrails live in `SKILL.md`; this file is only the data contracts.

## Input schema

Collect or infer any available subset. Mark missing fields as unknown rather than guessing.

```json
{
  "traveler_id": "string",
  "trip_id": "string",
  "event_type": "PickupDelayOrMissed | RentalLocationClosed | BookingCancelled | VehicleClassUnavailable | NoShowRisk | DropOffDelayRisk | GroundTransferDelayOrCancel",
  "disruption_origin": "primary_car | cascading_from_flight | cascading_from_hotel | cascading_from_activity",
  "booking": {
    "type": "rental_car | ground_transfer",
    "supplier": "string",
    "confirmation": "string",
    "vehicle_class": "string | null",
    "pickup_location": "string",
    "pickup_time": "datetime",
    "dropoff_location": "string",
    "dropoff_time": "datetime",
    "location_hours": "string | null",
    "prepaid": "boolean | unknown"
  },
  "risk_signal": {
    "description": "string",
    "source": "supplier | provider_ops | gds | flight_status | manual",
    "confidence": "confirmed | probable | unverified"
  },
  "linked_context": {
    "flight_arrival_eta": "datetime | unknown",
    "hotel_checkin": "datetime | null",
    "anchored_activities": [],
    "anchored_meetings": []
  },
  "traveler_context": {
    "current_location": "string | null",
    "accessibility": "string | null",
    "party_size": "integer | null",
    "priority": "string | null"
  },
  "policy": {
    "execution_mode": "report_only | traveler_confirm | ops_approval"
  }
}
```

## Output schema — PA Cascade Report

Compact JSON shape for system-facing output. This is a report-and-advise payload: it carries reasoning, severity, the full cascade, and the recovery posture, but no supplier contact, rebooking, or payment change is executed here. `severity` and `pa_signal` are one of `HIGH | MEDIUM | LOW`, and `major_action_taken` stays `false` until approval is confirmed and executed.

```json
{
  "skill": "car-disruption-detection",
  "event_type": "PickupDelayOrMissed | RentalLocationClosed | BookingCancelled | VehicleClassUnavailable | NoShowRisk | DropOffDelayRisk | GroundTransferDelayOrCancel",
  "disruption_origin": "primary_car | cascading_from_flight | cascading_from_hotel | cascading_from_activity",
  "severity": "LOW | MEDIUM | HIGH | CRITICAL",
  "pa_signal": "LOW | MEDIUM | HIGH | CRITICAL",
  "confidence": "confirmed | probable | unverified",
  "reasoning": "why this severity, and how the car/transfer disruption cascades across the trip",
  "risk_summary": {
    "what": "",
    "booking": "",
    "when": "",
    "source": ""
  },
  "cascade_summary": {
    "pickup": "",
    "dropoff": "",
    "onward_transport": "",
    "hotel": "",
    "activities": "",
    "meetings": "",
    "flight_return": ""
  },
  "recovery_status": {
    "options_status": "AVAILABLE_FOR_REVIEW | IN_PROGRESS | NOT_REQUIRED | BLOCKED",
    "option_types": "hold_vehicle | alt_vehicle_class | alt_supplier | adjust_pickup_window | alt_ground_transfer",
    "execution_gate": "traveler_confirm | ops_approval"
  },
  "pa_guidance": "",
  "action_center": {
    "status": "monitoring | needs_traveler_confirmation | needs_ops_approval | executing | completed | blocked",
    "headline": "",
    "next_step": ""
  },
  "specific_recommendations_included": false,
  "major_action_taken": false
}
```

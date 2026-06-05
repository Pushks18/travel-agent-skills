# Stay Disruption Detection — Input & Output Schemas

Load this file when you need the exact field shapes for input parsing or the PA-facing cascade report. The operating principle, severity model, workflow, and cascade logic live in `SKILL.md`; this file is only the data contracts.

## Input schema

Collect or infer any available subset. Mark missing fields as unknown rather than guessing.

```json
{
  "use_case_id": "UC-067",
  "trip_id": "string",
  "traveler_id": "string",
  "original_hotel": {
    "name": "string",
    "address": "string",
    "chain_brand": "string",
    "room_type": "string",
    "rate": "string",
    "check_in": "date",
    "check_out": "date",
    "loyalty_tier": "string | null",
    "special_requests": []
  },
  "disruption": {
    "event_type": "HotelShutDown | HotelOverbooking | HotelBookingCancelled | PropertyClosureRenovation | SafetyEmergencyEvacuation",
    "cause": "property_driven | supplier_driven | safety_driven | traveler_impact_driven",
    "reason": "string",
    "confidence": "confirmed | probable | unverified"
  },
  "traveler_state": {
    "arrival_status": "pre_arrival | in_transit | at_property | checked_in | evacuated",
    "eta_to_original_property": "datetime | unknown",
    "special_requirements": []
  },
  "hotel_anchored_dependencies": {
    "car_rental": [],
    "activities": [],
    "transfers": [],
    "meetings": []
  }
}
```

## Output schema — PA Cascade Report

Compact JSON shape for system-facing output. This is a report-and-advise payload: it carries reasoning, severity, the full cascade, and the Ops-approval posture, but no major action is executed here. By default `severity` and `pa_signal` are one of `HIGH | MEDIUM | LOW`, and `major_action_taken` is `false` until Ops approval is confirmed and executed.

```json
{
  "use_case_id": "UC-067",
  "skill": "stay-disruption-detection",
  "event_type": "HotelShutDown | HotelOverbooking | HotelBookingCancelled | PropertyClosureRenovation | SafetyEmergencyEvacuation",
  "priority": "Trip-Critical",
  "severity": "LOW | MEDIUM | HIGH | CRITICAL",
  "pa_signal": "LOW | MEDIUM | HIGH | CRITICAL",
  "confidence": "confirmed | probable | unverified",
  "reasoning": "why this severity, and how the lodging failure cascades across the trip",
  "ops_approval_required": true,
  "major_action_taken": false,
  "traveler_state": {
    "arrival_status": "pre_arrival | in_transit | at_property | checked_in | evacuated",
    "eta_to_original_property": "unknown or timestamp",
    "special_requirements": []
  },
  "cascade_report": {
    "hotel": "original stay unavailable or at risk",
    "car_rental": "pickup/return location or timing impact",
    "activities": "pickup, refund, reschedule, or location impact",
    "transfers": "airport/hotel transfer reroute impact",
    "meetings_or_events": "arrival/location impact",
    "risk_summary": "plain-language summary"
  },
  "recovery_status": {
    "equivalent_property_search": "available | in_progress | blocked",
    "preferred_chain_policy": "prefer Marriott/Hilton tier or chain partnership where applicable",
    "supplier_expense_position": "same-rate or upgraded equivalent requested from original property/supplier",
    "ops_status": "pending_approval | approved | rejected | emergency_override"
  },
  "pa_guidance": "Tell traveler the original property is unavailable, the cascade has been assessed, and Ops is validating an equivalent replacement before final confirmation.",
  "action_center": {
    "status": "needs_ops_approval | recovery_in_progress | rebooked | blocked",
    "headline": "Stay disruption detected",
    "next_step": "Ops approval required before replacement stay is confirmed"
  }
}
```

# Experience Disruption Detection — Input & Output Schemas

Load this file when you need the exact field shapes for input parsing or the PA-facing cascade report. The operating principle, trigger conditions, severity model, cascade logic, and guardrails live in `SKILL.md`; this file is only the data contracts.

## Input schema

Collect or infer any available subset. Mark missing fields as unknown rather than guessing.

```json
{
  "traveler_id": "string",
  "trip_id": "string",
  "event_type": "ActivityCancelled | VenueClosed | EventRescheduled | MissedStartRisk | ProviderNoShowOrOverbooked | ReservationCancelled | CapacityOrAccessibilityIssue",
  "disruption_origin": "primary_experience | cascading_from_flight | cascading_from_car | cascading_from_hotel | cascading_from_external",
  "experience": {
    "type": "tour | attraction | event | show | excursion | class | dining_reservation",
    "name": "string",
    "provider": "string",
    "confirmation": "string",
    "location": "string",
    "start_time": "datetime",
    "end_time": "datetime | null",
    "meeting_point": "string | null",
    "pickup_included": "boolean | unknown",
    "prepaid": "boolean | unknown",
    "refundable": "boolean | unknown",
    "party_size": "integer | null"
  },
  "risk_signal": {
    "description": "string",
    "source": "provider | platform | venue | flight_status | ground_transport | manual",
    "confidence": "confirmed | probable | unverified"
  },
  "linked_context": {
    "arrival_eta": "datetime | unknown",
    "anchoring_transport": "flight | car | transfer | hotel_shuttle | null",
    "same_day_items": []
  },
  "traveler_context": {
    "accessibility": "string | null",
    "occasion": "string | null",
    "priority": "string | null"
  },
  "policy": {
    "execution_mode": "report_only | traveler_confirm | ops_approval"
  }
}
```

## Output schema — PA Cascade Report

Compact JSON shape for system-facing output. This is a report-and-advise payload: it carries reasoning, severity, the full cascade, and the recovery posture, but no provider contact, rebooking, refund, or payment change is executed here. `severity` and `pa_signal` are one of `HIGH | MEDIUM | LOW`, and `major_action_taken` stays `false` until approval is confirmed and executed.

```json
{
  "skill": "experience-disruption-detection",
  "event_type": "ActivityCancelled | VenueClosed | EventRescheduled | MissedStartRisk | ProviderNoShowOrOverbooked | ReservationCancelled | CapacityOrAccessibilityIssue",
  "disruption_origin": "primary_experience | cascading_from_flight | cascading_from_car | cascading_from_hotel | cascading_from_external",
  "severity": "LOW | MEDIUM | HIGH | CRITICAL",
  "pa_signal": "LOW | MEDIUM | HIGH | CRITICAL",
  "confidence": "confirmed | probable | unverified",
  "reasoning": "why this severity, and how the experience disruption cascades across the day and trip",
  "risk_summary": {
    "what": "",
    "experience": "",
    "when": "",
    "source": ""
  },
  "cascade_summary": {
    "experience": "",
    "same_day_activities": "",
    "anchoring_transport": "",
    "dining_or_reservations": "",
    "downstream_plans": "",
    "refund_or_reschedule": ""
  },
  "recovery_status": {
    "options_status": "AVAILABLE_FOR_REVIEW | IN_PROGRESS | NOT_REQUIRED | BLOCKED",
    "option_types": "reschedule | alt_provider | alt_experience | refund_or_credit | adjust_timing",
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

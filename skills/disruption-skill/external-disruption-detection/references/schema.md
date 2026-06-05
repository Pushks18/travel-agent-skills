# External Disruption Detection — Input & Output Schemas

Load this file when you need the exact field shapes for input parsing or the PA-facing cascade report. The operating principle, severity model, per-event handlers, and cascade logic live in `SKILL.md`; this file is only the data contracts.

## Input schema

Collect or infer any available subset. Mark missing fields as unknown rather than guessing.

```json
{
  "traveler_id": "string",
  "trip_id": "string",
  "use_case_id": "UC-069 | UC-070 | UC-071",
  "event_type": "NewsAround | WeatherStorm | TransportStrike",
  "risk_signal": {
    "category": "safety_incident | civil_unrest | severe_weather | strike | closure | other",
    "description": "string",
    "source": "news | govt_advisory | weather_service | transit_authority | provider_ops | manual",
    "confidence": "confirmed | probable | unverified",
    "geography": "country | region | city | airport | station | venue",
    "transport_mode": "flight | train | bus | ride | ferry | null",
    "time_window": {
      "starts": "datetime | null",
      "ends": "datetime | null"
    }
  },
  "itinerary": {
    "segments": [],
    "hotels": [],
    "car_rental": [],
    "activities": [],
    "transfers": [],
    "meetings": []
  },
  "traveler_context": {
    "current_location": "string | null",
    "accessibility": "string | null",
    "medical": "string | null",
    "party_size": "integer | null",
    "priority": "string | null"
  },
  "policy": {
    "execution_mode": "report_only | traveler_confirm | ops_approval | emergency_autonomous",
    "insurance_eligible": "boolean | unknown"
  }
}
```

## Output schema — PA Cascade Report

Compact JSON shape for system-facing output. This is a report-and-advise payload by default: it carries reasoning, severity, the full cascade, and the recovery posture. Specific options are shown only as a gated Traveler-Confirmed (Pre) menu, and `major_action_taken` stays `false` until traveler/Ops approval is confirmed and executed.

```json
{
  "use_case_id": "UC-069 | UC-070 | UC-071",
  "skill": "external-disruption-detection",
  "event_type": "NewsAround | WeatherStorm | TransportStrike",
  "posture": "Notify | Orchestrate | Coordinate",
  "severity": "LOW | MEDIUM | HIGH | CRITICAL",
  "pa_signal": "LOW | MEDIUM | HIGH | CRITICAL",
  "confidence": "confirmed | probable | unverified",
  "reasoning": "why this severity, and how the external event cascades across the trip",
  "risk_summary": {
    "what": "",
    "where": "",
    "when": "",
    "source": ""
  },
  "cascade_summary": {
    "flights": "",
    "hotel": "",
    "car_rental": "",
    "activities": "",
    "transfers": "",
    "meetings": "",
    "traveler_safety": ""
  },
  "recovery_status": {
    "options_status": "AVAILABLE_FOR_REVIEW | IN_PROGRESS | NOT_REQUIRED | BLOCKED",
    "option_types": "protective_rebook | reroute_alt_mode | reschedule | insurance_claim",
    "execution_gate": "traveler_confirm | ops_approval | emergency_autonomous"
  },
  "pa_guidance": "",
  "action_center": {
    "status": "monitoring | needs_traveler_confirmation | needs_ops_approval | executing | completed | blocked",
    "headline": "",
    "next_step": ""
  },
  "ops_audit_required": true,
  "specific_recommendations_included": false,
  "major_action_taken": false
}
```

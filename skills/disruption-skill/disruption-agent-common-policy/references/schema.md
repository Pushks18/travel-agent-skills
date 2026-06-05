# Disruption Agent Common Policy — Shared Schemas

These are the canonical data contracts every Disruption Detection Agent skill must use. Load this file when building a cascade report, a PA notification payload, or an Action Center entry. The policy rules themselves live in `SKILL.md`.

MICE = Meetings, Incentives, Conferences, Events.

## Cascade Impact Schema

The shared per-layer impact structure. Every domain skill fills the layers it can assess and marks the rest `unknown`. A skill must not overwrite a layer that another skill owns as a primary event — report it as a cascade reference instead.

```json
{
  "cascade_impact": {
    "flight":            { "status": "unaffected | at_risk | delayed | missed | cancelled | unknown", "detail": "" },
    "hotel":             { "status": "unaffected | check_in_shift | at_risk | unavailable | unknown", "detail": "" },
    "car":               { "status": "unaffected | pickup_shift | no_show_risk | unavailable | unknown", "detail": "" },
    "transfer":          { "status": "unaffected | reschedule_needed | at_risk | cancelled | unknown", "detail": "" },
    "activity":          { "status": "unaffected | missed_start_risk | cancelled | reschedule_needed | unknown", "detail": "" },
    "mice":              { "status": "unaffected | arrival_risk | location_impact | unknown", "detail": "" },
    "traveler_schedule": { "status": "unaffected | tightened | broken | unknown", "detail": "" }
  }
}
```

## PA Notification Payload Format

The unified payload every skill sends to the PA. Specific recovery options are gated; `major_action_taken` stays `false` until an approval gate is cleared and execution completes.

```json
{
  "schema_version": "1.0",
  "source_skill": "string",
  "use_case_id": "string | null",
  "event_type": "string",
  "event_role": "primary | cascading",
  "primary_event_ref": "string | null",
  "dedup_key": "string",
  "severity": "LOW | MEDIUM | HIGH | CRITICAL",
  "pa_signal": "LOW | MEDIUM | HIGH | CRITICAL",
  "confidence": "confirmed | probable | unverified",
  "reasoning": "why this severity, and how it cascades",
  "summary": "plain-language disruption summary",
  "cascade_impact": { "see": "Cascade Impact Schema" },
  "recovery_status": {
    "options_status": "AVAILABLE_FOR_REVIEW | IN_PROGRESS | NOT_REQUIRED | BLOCKED",
    "execution_gate": "traveler_confirm | ops_approval | emergency_autonomous"
  },
  "pa_guidance": "what the PA should tell/ask the traveler next",
  "status": "Detected | Assessed | ReportedToPA | WaitingApproval | Approved | Executed | Resolved | Failed",
  "specific_recommendations_included": false,
  "major_action_taken": false,
  "audit": {
    "detected_at": "datetime",
    "source": "string",
    "correlation_id": "string"
  }
}
```

## Action Center Output Format

```json
{
  "action_center_card": {
    "title": "string",
    "source_skill": "string",
    "event_role": "primary | cascading",
    "severity": "LOW | MEDIUM | HIGH | CRITICAL",
    "status": "Detected | Assessed | ReportedToPA | WaitingApproval | Approved | Executed | Resolved | Failed",
    "headline": "string",
    "next_step": "string",
    "items": [
      {
        "type": "flight | hotel | car | transfer | activity | mice",
        "impact": "string",
        "status": "pending | approved | contacted | rebooked | refunded | failed | unknown"
      }
    ],
    "approval_required": true,
    "audit_ref": "correlation_id"
  }
}
```

# Disruption Agent Common Policy — Golden Examples

Canonical worked examples for the cross-cutting decisions every disruption skill makes. These are **governed fixtures**: each one's `severity` and `event_role` must stay consistent with the rules in `SKILL.md`. If a rule changes, update the matching example (and any CI/eval check) in the same change. Domain skills should follow these patterns rather than inventing their own.

Each example shows the input the skill received and the PA Notification Payload it should produce (see [schema.md](schema.md#pa-notification-payload-format)). Values are illustrative.

---

## Example A — Severity boundary (HIGH vs CRITICAL)

The decision: a confirmed disruption with downstream cascade, but a recovery path still exists → **HIGH**, not CRITICAL. CRITICAL is reserved for safety/stranding with no viable recovery.

**Input (to flight-disruption-detection):**

```json
{
  "trip_id": "TRIP-3382",
  "event_type": "FLIGHT_CANCEL",
  "flight": { "flight_number": "AA231", "arrival_airport": "LHR", "scheduled_arrival": "2026-06-10T19:40Z", "airline_rebooking_status": "pending" },
  "downstream_items": { "hotel": [{ "check_in": "2026-06-10" }], "connections": [] }
}
```

**Correct PA payload (abridged):**

```json
{
  "source_skill": "flight-disruption-detection",
  "event_type": "FLIGHT_CANCEL",
  "event_role": "primary",
  "primary_event_ref": null,
  "dedup_key": "TRIP-3382:AA231:flight",
  "severity": "HIGH",
  "confidence": "confirmed",
  "reasoning": "Flight cancelled with no confirmed rebooking; pushes same-day hotel check-in. A same-day recovery path still plausibly exists and traveler safety is not threatened, so HIGH — not CRITICAL.",
  "cascade_impact": {
    "flight": { "status": "cancelled", "detail": "AA231 cancelled, rebooking pending" },
    "hotel": { "status": "check_in_shift", "detail": "late/at-risk check-in on 2026-06-10" },
    "car": { "status": "unknown", "detail": "" },
    "transfer": { "status": "unknown", "detail": "" },
    "activity": { "status": "unknown", "detail": "" },
    "mice": { "status": "unknown", "detail": "" },
    "traveler_schedule": { "status": "tightened", "detail": "arrival day disrupted" }
  },
  "recovery_status": { "options_status": "AVAILABLE_FOR_REVIEW", "execution_gate": "traveler_confirm" },
  "status": "ReportedToPA",
  "major_action_taken": false
}
```

> If instead the traveler were stranded overnight with no same-day recovery and a missed time-critical commitment, the same event would be `CRITICAL`.

---

## Example B — Primary vs cascading (defer ownership, don't duplicate)

The decision: a car no-show caused by the same cancelled flight is **cascading**, owned by the flight event — not a new primary disruption. The car skill reports its layer only and sets `primary_event_ref`.

**Input (to car-disruption-detection), same trip as Example A:**

```json
{
  "trip_id": "TRIP-3382",
  "event_type": "NoShowRisk",
  "booking": { "type": "rental_car", "pickup_location": "LHR T5", "pickup_time": "2026-06-10T20:30Z" },
  "linked_context": { "flight_arrival_eta": "unknown" }
}
```

**Correct PA payload (abridged):**

```json
{
  "source_skill": "car-disruption-detection",
  "event_type": "NoShowRisk",
  "event_role": "cascading",
  "primary_event_ref": "TRIP-3382:AA231:flight",
  "dedup_key": "TRIP-3382:AA231:car",
  "severity": "HIGH",
  "confidence": "probable",
  "reasoning": "Car pickup at LHR T5 is at no-show risk because the anchoring flight AA231 was cancelled. This is a cascade from the flight event — ownership stays with flight-disruption-detection; this report covers the car layer only and does not re-score the flight.",
  "cascade_impact": {
    "flight": { "status": "cancelled", "detail": "ref primary TRIP-3382:AA231:flight — not re-scored here" },
    "car": { "status": "no_show_risk", "detail": "pickup 20:30 may be unattended if arrival slips" },
    "hotel": { "status": "unknown", "detail": "" },
    "transfer": { "status": "unknown", "detail": "" },
    "activity": { "status": "unknown", "detail": "" },
    "mice": { "status": "unknown", "detail": "" },
    "traveler_schedule": { "status": "tightened", "detail": "ground transport at risk" }
  },
  "recovery_status": { "options_status": "AVAILABLE_FOR_REVIEW", "execution_gate": "traveler_confirm" },
  "status": "ReportedToPA",
  "major_action_taken": false
}
```

> The car skill must **not** emit `event_role: primary` here. One root cause (the cancellation) → one primary alert (flight) + cascade references (car, hotel), never multiple primaries.

---

## Example C — Deduplication (attach, don't re-alert)

The decision: a second signal for an already-reported root event must **merge as a status/severity update**, not raise a new PA alert. Matching is by `dedup_key` / `primary_event_ref`.

**Input:** a fresh weather feed re-confirms the same storm already reported for `dedup_key TRIP-9001:STORM-77:flight` 20 minutes earlier, now with higher confidence.

**Correct behavior:**

```json
{
  "action": "update_existing",
  "dedup_key": "TRIP-9001:STORM-77:flight",
  "suppress_new_pa_alert": true,
  "update": {
    "confidence": "confirmed",
    "severity": "HIGH",
    "status": "ReportedToPA",
    "note": "Same root event within dedup window — sent as an update to the existing primary alert, not a duplicate notification."
  }
}
```

> Rule: within the dedup window, one root cause yields one PA thread. New information updates `confidence`/`severity`/`status` on the existing record; it does not generate a second alert.

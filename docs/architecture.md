# Travel Agent Skills Platform — Architecture

**Version:** 1.1 | **Date:** 2026-06-04

---

## Full System Diagram

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                        SKILL AUTHORING LAYER                                    ║
║                   github.com/Tabhi-Commons/travel-agent-skills                  ║
║                                                                                  ║
║  ┌─────────────────────────────────────────────────────────────────────────┐    ║
║  │  skills/                          CLI  (pip install -e .)               │    ║
║  │  ├── flight-search/SKILL.md       ┌─────────────────────────────────┐   │    ║
║  │  ├── hotel-search/SKILL.md        │ skills create  <name>           │   │    ║
║  │  ├── booking-skill/SKILL.md       │ skills generate <desc> --name   │   │    ║
║  │  ├── fare-rules/SKILL.md          │ skills validate --all           │   │    ║
║  │  ├── modify-booking/SKILL.md      │ skills package  <name>          │   │    ║
║  │  ├── ancillery-skill/SKILL.md     │ skills list / info              │   │    ║
║  │  └── planning-skill/SKILL.md      └─────────────────────────────────┘   │    ║
║  │                                                                           │    ║
║  │  registry.yaml  ← tracks version, owners, status, tags, distribution     │    ║
║  │  releases/      ← ZIP artifacts (org-provisioned, manual upload)         │    ║
║  └─────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                  ║
║  ┌──────────────────────────── GitHub Actions ─────────────────────────────┐    ║
║  │  Trigger: PR opened/updated touching skills/**                          │    ║
║  │                                                                          │    ║
║  │  ┌─── Job 1: validate ───┐       ┌─── Job 2: eval ──────────────────┐  │    ║
║  │  │ skills validate --all │──────▶│ checkout skill-testing-playground │  │    ║
║  │  │                       │ PASS  │ detect changed skill (git diff)   │  │    ║
║  │  │ FAIL → block PR ✗     │       │ start mock MCP server             │  │    ║
║  │  └───────────────────────┘       │ ab_compare --skill-path <dir>     │  │    ║
║  │                                  │          --trials 5               │  │    ║
║  │                                  │ post PR comment (verdict badge)   │  │    ║
║  │                                  └──────────────────────────────────┘  │    ║
║  └─────────────────────────────────────────────────────────────────────────┘    ║
╚══════════════════════════════════════════════════════════════════════════════════╝
                                        │ checkout (read-only, EVAL_PLATFORM_TOKEN)
                                        ▼
╔══════════════════════════════════════════════════════════════════════════════════╗
║                         EVAL PLATFORM LAYER                                     ║
║                github.com/Tabhi-Commons/skill-testing-playground                ║
║                                                                                  ║
║  ┌────────────────┐   ┌──────────────────────────────────────────────────────┐  ║
║  │  Skill Loader  │   │                   A/B Harness                        │  ║
║  │                │   │                                                      │  ║
║  │ load_skill(p)  │   │  Input: skill_path, task list, N trials              │  ║
║  │ ┌────────────┐ │   │                                                      │  ║
║  │ │YAML front- │ │   │  For each task:                                      │  ║
║  │ │matter strip│ │   │   ├── condition A: no_skill  → agent(no prompt)      │  ║
║  │ └─────┬──────┘ │   │   └── condition B: with_skill → agent(skill.body)   │  ║
║  │       │ .body  │   │                                                      │  ║
║  └───────┼────────┘   │  N trials × 2 conditions per task                   │  ║
║          │            │  best-of-N score selected per condition              │  ║
║          ▼            └──────────────────────────┬───────────────────────────┘  ║
║  ┌───────────────────────────────────────────┐   │ ABResult[]                   ║
║  │              Travel Agent                 │   ▼                              ║
║  │         (LangGraph + LangChain)           │  ┌───────────────────────────┐  ║
║  │                                           │  │      Gate Check           │  ║
║  │  System prompt = skill.body (or empty)    │  │                           │  ║
║  │                                           │  │ weighted_delta =          │  ║
║  │  Tools:                                   │  │   Σ(delta × weight) / Σw  │  ║
║  │  ├── search_flights                       │  │                           │  ║
║  │  ├── search_hotels        ◀── Mock MCP    │  │ T1 BLOCK  delta < -0.05   │  ║
║  │  ├── create_booking            (FastAPI)  │  │           OR regression   │  ║
║  │  ├── get_fare_rules                       │  │           rate > 50%      │  ║
║  │  ├── modify_booking                       │  │                           │  ║
║  │  ├── check_availability                   │  │ T2 SOFT   delta < 0       │  ║
║  │  ├── validate_passenger                   │  │ BLOCK     OR reg > 20%    │  ║
║  │  ├── add_ancillary                        │  │                           │  ║
║  │  └── get_itinerary                        │  │ T3 WARN   small neg delta │  ║
║  └─────────────────────────────────┬─────────┘  │                           │  ║
║                                    │            │ PASS      delta ≥ +0.05   │  ║
║                        agent output│            │           reg < 20%       │  ║
║                                    ▼            └─────────────┬─────────────┘  ║
║  ┌──────────────────────────────────────┐                     │ GateDecision    ║
║  │           Verifier                   │                     │                 ║
║  │                                      │                     ▼                 ║
║  │  ToolCallVerifier                    │        ┌────────────────────────────┐ ║
║  │   required_tools ✓                   │        │  ab_results.json           │ ║
║  │   required_params ✓                  │        │  {                         │ ║
║  │   score: 0.0–1.0                     │        │    weighted_delta: +0.142  │ ║
║  │                                      │        │    regression_rate: 0.0    │ ║
║  │  LLMJudgeVerifier                    │        │    verdict: "PASS"         │ ║
║  │   instruction-based scoring          │        │    flagged_tasks: []       │ ║
║  │   score: 0.0–1.0                     │        │    tasks: [...]            │ ║
║  └──────────────────────────────────────┘        │  }                         │ ║
║                                                   └────────────────────────────┘ ║
║                                                                                  ║
║  ┌──────────────────────────────────────────────────────────────────────────┐   ║
║  │  Trajectory Store (SQLite)       LangSmith Tracing                       │   ║
║  │  per-step: tool, latency, tokens  per-run: full LLM call tree            │   ║
║  │  failure modes: 7 categories      session_id: task_id + run_id           │   ║
║  └──────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                  ║
║  ┌──────────────────────────────────────────────────────────────────────────┐   ║
║  │  GRPO Optimizer (propose-only)                                           │   ║
║  │  cluster failed tasks by domain + failure mode                           │   ║
║  │  → propose skill edits (existing) OR new skill PR (Phase 6)             │   ║
║  └──────────────────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════════════╝
                                        │
                        ┌───────────────┼────────────────┐
                        ▼               ▼                ▼
                ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
                │  Leaderboard │ │  PR Comment  │ │  ZIP Releases    │
                │  (weighted Δ │ │  verdict     │ │  (Claude upload, │
                │   per skill) │ │  badge + link│ │   org-provision) │
                └──────────────┘ └──────────────┘ └──────────────────┘
```

---

## Dynamic Skill Creation Paths (Phase 6)

```
PATH A — `skills generate` (human-initiated, LLM-drafted)
─────────────────────────────────────────────────────────

  Engineer types:
  $ skills generate "Handle disruptions and rebooking" --name disruption-handling

          │
          ▼
  ┌───────────────────────────────────────────────────┐
  │  generate command                                  │
  │  1. validate name (format check)                  │
  │  2. call LLM (Claude Haiku) with GENERATE_PROMPT  │
  │     Input:  name + description                    │
  │     Output: markdown body (workflow + tables)     │
  │  3. prepend YAML frontmatter                      │
  │  4. write skills/disruption-handling/SKILL.md     │
  │  5. register in registry.yaml (status: draft)     │
  └───────────────────────────────────────────────────┘
          │
          ▼
  Human reviews + edits SKILL.md
          │
          ▼
  Opens PR → CI eval gate runs → PASS/BLOCK/WARN
          │ PASS
          ▼
  Merged to main ✓


PATH B — GRPO auto-proposal (system-initiated, triggered by failures)
─────────────────────────────────────────────────────────────────────

  Eval run completes → 8 failed tasks in "disruption" domain, no skill exists
          │
          ▼
  ┌────────────────────────────────────────────────────────┐
  │  GRPO Optimizer                                         │
  │  1. cluster failures: domain=disruption, 8 tasks        │
  │  2. no existing skill covers this domain                │
  │  3. call LLM: draft SKILL.md body from failure context  │
  │  4. call GitHub API:                                    │
  │     - create branch: proposal/disruption-handling       │
  │     - write skills/disruption-handling/SKILL.md         │
  │     - open PR: "proposal: auto-generated skill"         │
  └────────────────────────────────────────────────────────┘
          │
          ▼
  PR opens → CI eval gate runs automatically
          │
          ├── BLOCK → PR flagged, human must fix before merge
          ├── PASS  → human reviews content, approves or closes
          └── Auto-merge never happens — human approves every time
```

---

## Task Bank → Skill Routing

```
User message arrives at travel agent
          │
          ▼
  ┌───────────────────────────────────────────────────────────────────┐
  │  Skill detection (description-based routing)                       │
  │                                                                    │
  │  "find flights JFK to LAX July 10"   → flight-search              │
  │  "book FL123 for Alice Johnson"       → booking-skill             │
  │  "hotels near downtown Seattle"       → hotel-search              │
  │  "can I cancel my ticket"             → fare-rules                │
  │  "change my return date to July 15"   → modify-booking            │
  │  "add extra legroom seat"             → ancillery-skill            │
  │  "plan 4-day trip to Tokyo"           → planning-skill            │
  └───────────────────────────────────────────────────────────────────┘
          │
          ▼
  Matched skill.body injected into agent system prompt
  Agent calls mock MCP tools, verifier scores the output
```

---

## End-to-End Example: Engineer adds `hotel-search` skill

```
Day 0 — Authoring
──────────────────
  $ cd travel-agent-skills
  $ skills create hotel-search --owner travel-platform --with-references
  → skills/hotel-search/SKILL.md scaffolded (template body)
  → registry.yaml entry created (status: draft)

  Engineer writes the full SKILL.md:
  - Workflow: confirm inputs → search → filter → rank → format → trade-offs
  - Required: destination, check-in, check-out, guest count
  - Optional: star rating, max price, amenities, cancellation policy
  - Edge cases: same-day in/out, no results, group bookings

  $ skills validate hotel-search
  → PASS ✓

Day 1 — Pull Request opened
────────────────────────────
  $ git add skills/hotel-search/SKILL.md registry.yaml
  $ git commit -m "feat: add hotel-search skill"
  $ gh pr create --title "feat: add hotel-search skill"

  GitHub Actions triggers (.github/workflows/eval.yml):
  │
  ├── Job: validate
  │   $ skills validate --all
  │   ALL 7 SKILLS PASS ✓
  │
  └── Job: eval
      Checks out skill-testing-playground @ main
      Detects changed skill: skills/hotel-search
      Starts mock MCP server on :8000
      Runs:
        python -m eval.ab_compare \
          --skill-path skills/hotel-search \
          --trials 5
      │
      │  10 hotel-search tasks × 5 trials × 2 conditions = 100 agent runs
      │
      │  Task results:
      │  hotel-search-001  weight=2.0  no=0.40  with=0.85  Δ=+0.45  +
      │  hotel-search-002  weight=2.0  no=0.60  with=0.90  Δ=+0.30  +
      │  hotel-search-003  weight=2.0  no=0.20  with=0.80  Δ=+0.60  +
      │  hotel-search-004  weight=2.0  no=0.80  with=0.80  Δ=+0.00  -
      │  hotel-search-005  weight=2.0  no=0.40  with=0.75  Δ=+0.35  +
      │  ...
      │
      │  Weighted delta:   +0.312
      │  Regression rate:  0%
      │  Gate verdict:     PASS (Tier 0)
      │
      Posts PR comment:
      ┌──────────────────────────────────────────────────────┐
      │ ✅ Skill Eval: `hotel-search` — PASS                 │
      │                                                       │
      │ Metric           Value                               │
      │ Weighted Δ       +0.312                              │
      │ Regression rate  0.0%                                │
      │ Verdict          PASS                                │
      └──────────────────────────────────────────────────────┘

Day 1 — Merge
──────────────
  PR approved + merged to main ✓
  
  Post-merge (future Phase 3):
  - Leaderboard updated: hotel-search Δ=+0.312 added
  - ZIP packaged: releases/hotel-search/0.1.0/hotel-search.zip
  - Org-provisioned distribution triggered
```

---

## Secrets Required

| Secret | Repo | Purpose |
|--------|------|---------|
| `EVAL_PLATFORM_TOKEN` | travel-agent-skills | Read access to skill-testing-playground |
| `OPENROUTER_API_KEY` | travel-agent-skills | LLM calls in eval agent |
| `LANGSMITH_API_KEY` | travel-agent-skills | Trace uploads (optional) |
| `GITHUB_TOKEN` | skill-testing-playground | Auto-provided by Actions; used by GRPO PR opener |
| `ANTHROPIC_API_KEY` | skill-testing-playground | `skills generate` LLM calls (Phase 6) |

---

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Connect repos — skill loader, CI, --skill-path, task bank alignment | ✅ done |
| 2 | Langfuse observability — replace SQLite trajectory store | ⏳ next |
| 3 | Web platform — FastAPI + Next.js leaderboard + skill editor | ⏳ planned |
| 4 | Skill portability — /commands export + REST API | ⏳ planned |
| 5 | Multi-model eval + gate calibration | ⏳ planned |
| 6 | Dynamic skill creation — `skills generate` + GRPO auto-proposal | ⏳ planned |

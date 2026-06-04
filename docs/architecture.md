# Travel Agent Skills Platform — Architecture

**Version:** 1.2 | **Date:** 2026-06-04

---

## Full System Diagram

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                        SKILL AUTHORING LAYER                                         ║
║                   github.com/Tabhi-Commons/travel-agent-skills                       ║
║                                                                                      ║
║  skills/                              CLI  (pip install -e .)                        ║
║  ├── flight-search/SKILL.md           ┌──────────────────────────────────────────┐  ║
║  ├── hotel-search/SKILL.md            │ skills create   <name> --owner <team>    │  ║
║  ├── booking-skill/SKILL.md           │ skills generate <name> --description "…" │  ║
║  ├── fare-rules/SKILL.md              │   └─ Gemini 2.5 Flash via OpenRouter     │  ║
║  ├── modify-booking/SKILL.md          │ skills validate --all                    │  ║
║  ├── ancillery-skill/SKILL.md         │ skills package  <name>                   │  ║
║  └── planning-skill/SKILL.md          │ skills list / info / delete              │  ║
║                                       └──────────────────────────────────────────┘  ║
║  registry.yaml  ← version, owners, status, tags, distribution                       ║
║  releases/      ← ZIP artifacts  (org-provisioned, manual upload, project-local)    ║
║                                                                                      ║
║  ┌────────────────────────── GitHub Actions (.github/workflows/eval.yml) ──────────┐ ║
║  │  Trigger: PR opened/updated on skills/**                                        │ ║
║  │                                                                                  │ ║
║  │  Job 1 — validate          Job 2 — eval  (needs: validate)                      │ ║
║  │  ┌────────────────────┐    ┌────────────────────────────────────────────────┐   │ ║
║  │  │ skills validate    │───▶│ checkout skill-testing-playground (read-only)  │   │ ║
║  │  │ --all              │    │ detect changed skill  (git diff HEAD^1)        │   │ ║
║  │  │ FAIL → block PR    │    │ start mock MCP server                          │   │ ║
║  │  └────────────────────┘    │ ab_compare --skill-path <dir> --trials 5       │   │ ║
║  │                             │ post PR comment (verdict + Langfuse links)     │   │ ║
║  │                             └────────────────────────────────────────────────┘   │ ║
║  │  Secrets required:                                                               │ ║
║  │  EVAL_PLATFORM_TOKEN  OPENROUTER_API_KEY  LANGFUSE_PUBLIC_KEY                   │ ║
║  │  LANGFUSE_SECRET_KEY  LANGFUSE_HOST                                              │ ║
║  └──────────────────────────────────────────────────────────────────────────────────┘ ║
╚════════════════════════════════════════════╤═════════════════════════════════════════╝
                                             │ checkout (read-only, EVAL_PLATFORM_TOKEN)
                                             ▼
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                         EVAL PLATFORM LAYER                                          ║
║                github.com/Tabhi-Commons/skill-testing-playground                     ║
║                                                                                      ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐ ║
║  │  Skill Loader  (eval/skill_loader.py)                                           │ ║
║  │  load_skill(path) → LoadedSkill(name, description, body, version, author)       │ ║
║  │  Strips YAML frontmatter → injects .body into agent system prompt               │ ║
║  │  Falls back to plain markdown for legacy skills                                  │ ║
║  └──────────────────────────────┬──────────────────────────────────────────────────┘ ║
║                                 │ skill.body                                         ║
║  ┌──────────────────────────────▼──────────────────────────────────────────────────┐ ║
║  │  A/B Harness  (eval/ab_compare.py)                                              │ ║
║  │                                                                                  │ ║
║  │  --skill-path <absolute-path>   ← accepts any SKILL.md dir from any repo        │ ║
║  │  --trials N                                                                      │ ║
║  │                                                                                  │ ║
║  │  Task loading: load_tasks_for_skill(skill_name, skill_path)                     │ ║
║  │   1. Exact match on task.toml  skill = "<name>"  (primary)                      │ ║
║  │   2. Semantic fallback via SkillRouter  (cosine sim, threshold 0.35)            │ ║
║  │                                                                                  │ ║
║  │  Per task × N trials:                                                           │ ║
║  │   condition A: no_skill  → agent(no system prompt skill)                        │ ║
║  │   condition B: with_skill → agent(skill.body injected)                          │ ║
║  │   best-of-N score selected per condition                                        │ ║
║  └──────────────────────────────┬──────────────────────────────────────────────────┘ ║
║                                 │                                                     ║
║          ┌──────────────────────┼───────────────────────┐                            ║
║          ▼                      ▼                        ▼                            ║
║  ┌───────────────┐   ┌──────────────────────┐   ┌──────────────────────────────┐    ║
║  │ Travel Agent  │   │ Verifiers            │   │ Semantic Router              │    ║
║  │ (LangGraph)   │   │                      │   │ (eval/skill_router.py)       │    ║
║  │               │   │ ToolCallVerifier     │   │                              │    ║
║  │ System prompt │   │  checks tool name +  │   │ all-MiniLM-L6-v2 (80MB)     │    ║
║  │ = skill.body  │   │  param key presence  │   │ embed skill descriptions     │    ║
║  │ (or empty)    │   │  score: 0.0–1.0      │   │ cosine sim on instruction    │    ║
║  │               │   │  deterministic       │   │ → route to best-match skill  │    ║
║  │ Tools via     │   │                      │   │ <1ms / query after load      │    ║
║  │ Mock MCP ──── │──▶│ LLMJudgeVerifier     │   └──────────────────────────────┘    ║
║  │ :8000         │   │  Gemini 2.5 Flash    │                                        ║
║  └───────────────┘   │  via OpenRouter      │                                        ║
║                       │  criteria-aware      │                                        ║
║                       │  3 runs → averaged   │                                        ║
║                       │  score: 0.0–1.0      │                                        ║
║                       └──────────┬───────────┘                                        ║
║                                  │ EvalResult                                         ║
║                                  ▼                                                     ║
║  ┌──────────────────────────────────────────────────────────────────────────────────┐ ║
║  │  Gate Check  (eval/gate_check.py)                                                │ ║
║  │                                                                                  │ ║
║  │  weighted_delta = Σ(delta × domain_weight) / Σ(weights)                        │ ║
║  │                                                                                  │ ║
║  │  Domain weights:  booking_flow=3.0  flight/hotel_search=2.0                     │ ║
║  │                   itinerary_build=1.5  fare_rules=1.0  edge_cases=0.5           │ ║
║  │                                                                                  │ ║
║  │  T1 BLOCK      delta < -0.05  OR  critical task regressed > 15%  exit(1)        │ ║
║  │  T2 SOFT BLOCK delta < 0      OR  regression rate > 20%           exit(1)        │ ║
║  │  T3 WARN       small negative delta, overall positive             exit(0)        │ ║
║  │  PASS          delta ≥ +0.05, regression rate < 20%               exit(0)        │ ║
║  └──────────────────────────────┬───────────────────────────────────────────────────┘ ║
║                                 │ GateDecision + ABResult[]                           ║
║                                 ▼                                                     ║
║  ┌──────────────────────────────────────────────────────────────────────────────────┐ ║
║  │  Cost + Latency Metrics  (eval/cost.py)                                         │ ║
║  │                                                                                  │ ║
║  │  Per run:  input_tokens, output_tokens, cost_usd, latency_ms                    │ ║
║  │  Per eval: total_cost, avg_cost/run, avg_latency_ms, p95_latency_ms             │ ║
║  │  Delta:    cost_delta_usd, latency_delta_ms  (with_skill vs no_skill)           │ ║
║  │                                                                                  │ ║
║  │  Pricing (via OpenRouter, USD/1M tokens):                                        │ ║
║  │  google/gemini-2.5-flash  $0.15 in / $0.60 out   ← default model everywhere    │ ║
║  │  google/gemini-2.5-pro    $1.25 in / $10.00 out                                 │ ║
║  │  openai/gpt-4.1-mini      $0.40 in / $1.60 out                                  │ ║
║  └──────────────────────────────┬───────────────────────────────────────────────────┘ ║
║                                 │                                                     ║
║         ┌───────────────────────┼────────────────────┐                               ║
║         ▼                       ▼                     ▼                               ║
║  ┌─────────────┐   ┌────────────────────────┐  ┌──────────────────────────────────┐  ║
║  │  ab_results │   │  Langfuse              │  │  SQLite Trajectory Store         │  ║
║  │  .json      │   │  (cloud.langfuse.com   │  │  (trajectory.db)                 │  ║
║  │             │   │   or self-hosted)      │  │                                  │  ║
║  │  summary:   │   │                        │  │  runs: task_id, condition,       │  ║
║  │  weighted_Δ │   │  Full LLM call tree    │  │        score, failure_mode       │  ║
║  │  regression │   │  Tool call spans       │  │  steps: tool, latency, tokens   │  ║
║  │  verdict    │   │  Token cost per node   │  │                                  │  ║
║  │  cost block │   │  verifier_score event  │  │  7 failure modes:                │  ║
║  │  trace URLs │   │  session per task+run  │  │  NO_TOOL_CALL, WRONG_TOOL,       │  ║
║  └──────┬──────┘   │  Langfuse link → PR    │  │  MISSING_PARAM,                  │  ║
║         │          └────────────────────────┘  │  MULTI_STEP_DROPOUT,             │  ║
║         │                                       │  PARTIAL_MATCH,                  │  ║
║         ▼                                       │  HALLUCINATED_ID, UNKNOWN        │  ║
║  ┌─────────────────────────────────────────┐    └──────────────────────────────────┘  ║
║  │  GRPO Optimizer  (eval/optimizer/)      │                                          ║
║  │                                         │                                          ║
║  │  optimizer.py  — improve existing skill │                                          ║
║  │   K variants × M rounds via LLM         │                                          ║
║  │   fast-eval scores each variant         │                                          ║
║  │   propose-only, never auto-commits      │                                          ║
║  │                                         │                                          ║
║  │  propose_skill.py  — new skill from gap │                                          ║
║  │   cluster failed runs by domain         │                                          ║
║  │   skip domains with existing skill      │                                          ║
║  │   draft SKILL.md via Gemini 2.5 Flash   │                                          ║
║  │   open PR → travel-agent-skills         │                                          ║
║  │   CI eval gate runs on the PR           │                                          ║
║  │   human approves or closes — never      │                                          ║
║  │   auto-merged                           │                                          ║
║  └─────────────────────────────────────────┘                                          ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
                                        │
           ┌────────────────────────────┼───────────────────────────┐
           ▼                            ▼                           ▼
  ┌─────────────────┐     ┌─────────────────────────┐   ┌───────────────────────┐
  │  PR Comment     │     │  Leaderboard            │   │  ZIP Releases         │
  │                 │     │  (ab_results per skill) │   │  (releases/ dir)      │
  │  ✅/⚠️/🚫 badge │     │                         │   │  org-provisioned      │
  │  weighted Δ     │     │  skill → weighted_delta │   │  manual upload        │
  │  regression %   │     │  sorted by delta        │   │  project-local        │
  │  per-task       │     │  cost + latency cols    │   └───────────────────────┘
  │  Langfuse links │     └─────────────────────────┘
  └─────────────────┘
```

---

## Dynamic Skill Creation (Phase 6)

```
PATH A — `skills generate`  (human-initiated, LLM-drafted)
──────────────────────────────────────────────────────────

  $ skills generate disruption-handling \
      --description "Handle cancelled flights and rebooking" \
      --owner travel-platform

          │
          ▼
  ┌───────────────────────────────────────────────────────┐
  │  generate command  (travel_agent_skills/commands/)    │
  │  1. validate name (VALID_SKILL_NAME regex)            │
  │  2. call Gemini 2.5 Flash via OpenRouter              │
  │     prompt: name + description → structured body      │
  │  3. prepend YAML frontmatter                          │
  │  4. write skills/<name>/SKILL.md  (status: draft)     │
  │  5. upsert registry.yaml entry                        │
  └───────────────────────────────────────────────────────┘
          │
          ▼
  Human reviews + edits → opens PR → CI eval gate → PASS/BLOCK


PATH B — GRPO auto-proposal  (system-initiated, from failures)
────────────────────────────────────────────────────────────────

  eval run completes →  trajectory.db has 5+ no_skill failures in "disruption"
  domain, no "disruption-handling" skill exists
          │
          ▼
  ┌────────────────────────────────────────────────────────────────┐
  │  propose_skill.py  (eval/optimizer/)                            │
  │  1. load_failure_clusters(trajectory.db, tasks/, threshold=5)  │
  │     OR load_clusters_from_ab_results(ab_results.json)          │
  │  2. skip domains with existing skill in travel-agent-skills     │
  │  3. draft_skill_body(cluster)                                   │
  │     Gemini 2.5 Flash: failure context → SKILL.md body          │
  │  4. open_skill_pr() via GitHub API                             │
  │     branch: proposal/disruption-handling                       │
  │     file:   skills/disruption-handling/SKILL.md               │
  │     PR:     "proposal: auto-generated disruption-handling"     │
  └────────────────────────────────────────────────────────────────┘
          │
          ▼
  CI eval gate runs automatically on the PR
  Human reviews, edits content, approves or closes
  Auto-merge never happens
```

---

## Semantic Skill Router

```
SkillRouter  (eval/skill_router.py)
────────────────────────────────────

  Initialization (once):
    load skill descriptions from SKILL.md frontmatter
    embed with all-MiniLM-L6-v2 (80MB, local, no API)
    store normalized vectors

  Query (< 1ms):
    embed instruction
    cosine similarity vs all skill vectors
    return best match above threshold (0.35)

  Used in two places:

  1. eval/ab_compare.py — task bank fallback
     exact match on task.toml `skill =` field first
     semantic match on instruction.md when no exact match

  2. agent/router.py (Phase 8) — runtime orchestrator
     route user message → specialized agent

  Accuracy on travel domain (7 test queries):
    ✅ "Find flights JFK to LAX"        → flight-search   (0.40)
    ✅ "Hotel in Paris for 3 nights"    → hotel-search    (0.37)
    ✅ "Cancellation fees for ticket"   → fare-rules      (0.35)
    ✅ "Change my return date"          → modify-booking  (0.53)
    ✅ "Book FL123 for Alice"           → flight-search   (0.35) *
    ✅ "Plan 4-day trip to Tokyo"       → planning-skill  (0.43)
    ⚠️ "Add extra legroom seat"         → modify-booking  (should be ancillery-skill)

  * booking-skill description needs stronger "confirm and finalize" keywords
```

---

## LLM Calls — One Model, One Key

All LLM calls across both repos use **`google/gemini-2.5-flash` via OpenRouter**.

```
Component                   Model                      Key
─────────────────────────── ────────────────────────── ──────────────────
Travel agent (run_task.py)  google/gemini-2.5-flash    OPENROUTER_API_KEY
LLM judge verifier          google/gemini-2.5-flash    OPENROUTER_API_KEY
GRPO optimizer variants     google/gemini-2.5-flash    OPENROUTER_API_KEY
GRPO propose_skill draft    google/gemini-2.5-flash    OPENROUTER_API_KEY
skills generate CLI         google/gemini-2.5-flash    OPENROUTER_API_KEY
```

Override for an individual run: `EVAL_MODEL=google/gemini-2.5-pro python -m eval.ab_compare …`

---

## Observability Stack

```
Agent run
  │
  ├── Langfuse CallbackHandler  (LANGFUSE_PUBLIC_KEY / SECRET_KEY)
  │    full LLM call tree, tool spans, latency per node, token cost
  │    verifier_score pushed after run
  │    session_id = task_id__run_id  (groups no_skill + with_skill)
  │    trace URL stored in EvalResult.langsmith_run_id
  │    → surfaced in PR comment for each regressed task
  │
  ├── SQLite trajectory.db  (local, lightweight)
  │    runs: task_id, condition, score, failure_mode
  │    steps: tool_name, latency_ms, tokens
  │    used by GRPO propose_skill to find failure clusters
  │
  └── ab_results.json  (project root, CI-consumable)
       weighted_delta, regression_rate, verdict, tier
       regression_traces: {task_id → langfuse_url}
       cost: {no_skill: {total_cost, avg_cost, avg_latency, p95_latency}}
```

---

## Data Flow: End-to-End

```
1. Engineer opens PR  →  skills/hotel-search/SKILL.md

2. GitHub Actions fires in travel-agent-skills
   └── Job 1: skills validate --all   (format check)
   └── Job 2: checkout skill-testing-playground @ main (read-only)
              detect changed skill from git diff
              start mock MCP server at :8000
              python -m eval.ab_compare
                --skill-path skills/hotel-search
                --trials 5

3. A/B eval: 15 tasks × 5 trials × 2 conditions = 150 agent runs
   ├── Skill loader strips YAML frontmatter → injects body
   ├── Semantic router matches tasks if no exact skill= field
   ├── Each run traced in Langfuse (session grouped by task)
   ├── Each run cost tracked (tokens × $/1M)
   └── Verifier scores each run (ToolCallVerifier or LLMJudgeVerifier)

4. Gate check
   ├── T1 BLOCK  → PR blocked, exit 1
   ├── T2 SOFT   → PR blocked (overridable), exit 1
   ├── T3 WARN   → PR passes, warning comment
   └── PASS      → PR passes, green comment

5. PR comment posted:
   ✅ Skill Eval: `hotel-search` — PASS
   Weighted Δ: +0.312 | Regression: 0% | Cost Δ: +$0.006
   [Regressed tasks with Langfuse trace links if any]

6. On merge → skill is in main, ready to package and distribute
```

---

## Secrets Reference

| Secret | travel-agent-skills | skill-testing-playground | Purpose |
|--------|:-------------------:|:------------------------:|---------|
| `OPENROUTER_API_KEY` | ✅ | ✅ | All LLM calls (Gemini 2.5 Flash) |
| `LANGFUSE_PUBLIC_KEY` | ✅ | ✅ | Trace uploads |
| `LANGFUSE_SECRET_KEY` | ✅ | ✅ | Trace uploads |
| `LANGFUSE_HOST` | ✅ | ✅ | `https://cloud.langfuse.com` |
| `EVAL_PLATFORM_TOKEN` | ✅ | — | PAT to read skill-testing-playground |
| `GITHUB_TOKEN` | auto | auto | PR creation (auto-provided by Actions) |

**Add secrets:** each repo → Settings → Secrets and variables → Actions → New repository secret.

---

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Connect repos — skill loader, CI, `--skill-path`, task bank alignment | ✅ done |
| 2 | Langfuse observability + semantic router + cost/latency metrics | ✅ done |
| 3 | Web platform — FastAPI + Next.js leaderboard + skill editor | ⏳ next |
| 4 | Skill portability — `/commands` export + REST API | ⏳ planned |
| 5 | Multi-model eval + gate calibration | ⏳ planned |
| 6.1 | `skills generate` — LLM-drafted skill via CLI | ✅ done |
| 6.2 | GRPO auto-proposal — cluster failures, open PR | ✅ done |
| 7 | Cost, latency, token metrics per eval run | ✅ done |
| 8 | Multi-agent orchestrator — router + specialized agents | ⏳ planned |

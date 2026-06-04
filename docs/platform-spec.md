# Travel Agent Skills Platform — Full Spec

**Version:** 1.0  
**Date:** 2026-06-04  
**Repos:**
- `travel-agent-skills` — source of truth for skill authoring, validation, packaging
- `skill-testing-playground` — eval platform: A/B testing, gate check, observability, UI

---

## Problem Statement

`travel-agent-skills` is a well-structured skill library with a working CLI but no quality loop. There is no way to know whether a skill actually improves agent behavior before it merges. Skills are authored by hand, validated for format only, and distributed as ZIPs — with no signal on whether they help or hurt.

The `skill-testing-playground` eval platform solves this, but currently runs in isolation with its own stub skills in a different format. The two repos need to be connected into a single end-to-end system.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│              travel-agent-skills (source of truth)                   │
│                                                                      │
│  skills/                        CLI (skills create/validate/package) │
│  ├── flight-search/SKILL.md     registry.yaml                        │
│  ├── booking-skill/SKILL.md     releases/ (ZIPs for Claude)          │
│  ├── ancillery-skill/SKILL.md                                        │
│  └── planning-skill/SKILL.md                                         │
│                                                                      │
│  GitHub Actions CI                                                   │
│  └── on PR to skills/** → trigger eval in skill-testing-playground  │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │ skill PR event
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│              skill-testing-playground (eval platform)                │
│                                                                      │
│  Skill Loader        A/B Harness         Gate Check                 │
│  (parse frontmatter  (no_skill vs        T1 BLOCK / T2 SOFT /       │
│   + markdown body)    with_skill,        T3 WARN / PASS             │
│                       N trials)                                      │
│                                                                      │
│  Trajectory Store    LangSmith           Leaderboard                │
│  (SQLite per-step    (traces per run)    (weighted delta per skill)  │
│   + failure modes)                                                   │
│                                                                      │
│  Web Platform                                                        │
│  ├── FastAPI backend (skill CRUD, eval runner, leaderboard API)      │
│  └── Next.js frontend (leaderboard, skill editor, observability)     │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                      Result posted back to PR
                      (weighted delta, regression rate, verdict)
```

---

## Current State (what exists today)

### travel-agent-skills ✅
- `skills create / validate / list / info / package / delete` CLI — fully working
- 4 skills: `flight-search` (full), `booking-skill`, `ancillery-skill`, `planning-skill` (all authored)
- `registry.yaml` tracking version, owners, status, tags, distribution per skill
- ZIP packaging for Claude distribution
- 51 tests, 92% coverage

### skill-testing-playground ✅
- A/B eval harness (`ab_compare.py`) — runs no_skill vs with_skill, N trials, writes results
- Tiered gate check (`gate_check.py`) — T1 hard block / T2 soft block / T3 warn / Pass
- 50-task BenchFlow task bank across 6 domains
- Mock MCP server (9 travel endpoints)
- LangSmith tracing via `@langsmith.traceable`
- SQLite trajectory store with 7 failure modes
- Streamlit UI: leaderboard, skill manager, trajectory viewer
- Skill coverage P/R, trigger eval (30 labeled requests)
- Pseudo-GRPO optimizer (propose-only, never auto-commits)
- SkillPyramid analyzer

### Gap: the two repos are not connected
- skill-testing-playground uses plain markdown skills (no YAML frontmatter)
- travel-agent-skills uses agentskills.io spec (YAML frontmatter + markdown body)
- No CI in travel-agent-skills
- Eval platform does not pull skills from travel-agent-skills

---

## What needs to be built

---

### Phase 1: Connect the repos (Week 1 priority)

**Goal:** Every PR to `travel-agent-skills/skills/**` automatically triggers an eval run and posts the result back to the PR.

#### 1.1 Update skill loader in skill-testing-playground

`eval/run_task.py` currently reads SKILL.md as plain text. It needs to strip YAML frontmatter and use only the markdown body for agent injection.

```python
# eval/skill_loader.py (new file)
import re, yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class LoadedSkill:
    name: str
    description: str
    body: str           # markdown body only (what gets injected into agent)
    version: str
    author: str
    raw_path: Path

def load_skill(path: Path) -> Optional[LoadedSkill]:
    """Parse agentskills.io SKILL.md: strip YAML frontmatter, return structured skill."""
    content = path.read_text()
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if match:
        frontmatter = yaml.safe_load(match.group(1)) or {}
        body = match.group(2).strip()
    else:
        frontmatter = {}
        body = content.strip()
    return LoadedSkill(
        name=frontmatter.get("name", path.parent.name),
        description=frontmatter.get("description", ""),
        body=body,
        version=frontmatter.get("metadata", {}).get("version", "0.1.0"),
        author=frontmatter.get("metadata", {}).get("author", ""),
        raw_path=path,
    )
```

`eval/run_task.py`'s `load_skill()` function needs to use this loader and inject `skill.body` (not raw file content) into the agent system prompt.

#### 1.2 Update task bank to match real skills

Current task bank uses skill names like `flight-search`, `hotel-search`, `book-itinerary`, `fare-rules`. These need to map to the real skill names in travel-agent-skills:

| task.toml skill field | travel-agent-skills skill |
|----------------------|--------------------------|
| `flight-search` | `flight-search` ✅ |
| `book-itinerary` | `booking-skill` (rename mapping needed) |
| `hotel-search` | needs a new `hotel-search` skill |
| `fare-rules` | needs a new `fare-rules` skill |
| `modify-booking` | covered by `booking-skill` |
| `ancillery` | `ancillery-skill` |

**Immediate action:** create `hotel-search` and `fare-rules` skills in travel-agent-skills, or update task bank skill references to match existing skill names.

#### 1.3 Add CI to travel-agent-skills

`.github/workflows/eval.yml` in travel-agent-skills:

```yaml
name: Skill Eval Gate
on:
  pull_request:
    paths: ['skills/**']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -e ".[dev]"
      - run: skills validate --all

  eval:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Checkout eval platform
        uses: actions/checkout@v4
        with:
          repository: Tabhi-Commons/skill-testing-playground
          path: eval-platform
          token: ${{ secrets.EVAL_PLATFORM_TOKEN }}
      - name: Detect changed skill
        id: skill
        run: |
          CHANGED=$(git diff --name-only HEAD^1 HEAD | grep 'skills/.*/SKILL.md' | head -1)
          echo "skill=$(dirname $CHANGED)" >> $GITHUB_OUTPUT
      - name: Run eval
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
        run: |
          cd eval-platform
          pip install -e .
          python eval/mock_mcp/server.py &
          SKILL_NAME=$(basename ${{ steps.skill.outputs.skill }})
          python -m eval.ab_compare --skill-path ../${{ steps.skill.outputs.skill }} --trials 5
      - name: Post PR comment
        uses: actions/github-script@v7
        with:
          script: |
            # read ab_results.json and post verdict
```

#### 1.4 Pass skill path directly to ab_compare

Currently `ab_compare.py` resolves skills from `skills/concrete/` or `skills/abstract/` inside skill-testing-playground. Add a `--skill-path` flag that accepts an absolute path to any SKILL.md directory, so eval can run against skills from travel-agent-skills directly.

---

### Phase 2: Proper Observability with Langfuse (Week 2)

**Goal:** Replace the SQLite trajectory store with Langfuse. Every agent run gets a full trace tree in Langfuse: LLM call, tool calls, latency, token cost, eval score.

#### Why Langfuse over SQLite

| SQLite (current) | Langfuse |
|-----------------|---------|
| Tool call names and latency only | Full LLM call tree: prompt, completion, tool, nested spans |
| No token cost breakdown | Token cost per node, per run, per skill |
| Custom failure classifier | Built-in eval score API |
| No session grouping | Sessions: group no_skill + with_skill runs for same task |
| Streamlit trajectory viewer (basic) | Production-grade trace UI, filter, search |

#### Integration plan

```python
# eval/run_task.py — replace LangChainInstrumentor with Langfuse
from langfuse.callback import CallbackHandler

def run_task(task_path, skill_path=None, condition="no_skill", ...):
    langfuse_handler = CallbackHandler(
        tags=[f"skill:{skill_name}", f"condition:{condition}", f"task:{task_id}"],
        session_id=f"{task_id}_{run_id}",
    )
    agent = build_travel_agent(skill_content=skill_content)
    result = agent.invoke({...}, config={"callbacks": [langfuse_handler]})
    
    # Push eval score to Langfuse
    langfuse_handler.langfuse.score(
        trace_id=langfuse_handler.get_trace_id(),
        name="verifier_score",
        value=vresult.score,
        comment=vresult.reason,
    )
```

Self-host Langfuse via Docker Compose (or use langfuse.com free tier):
```bash
git clone https://github.com/langfuse/langfuse
cd langfuse && docker compose up
# UI at http://localhost:3000
```

Keep SQLite failure classifier as a lightweight supplement — it runs locally and classifies failures without needing a Langfuse query.

---

### Phase 3: Web Platform — FastAPI + Next.js (Week 3-4)

**Goal:** Replace Streamlit with a production-grade web UI. Streamlit works for prototyping; it's not suitable for a team-facing platform.

#### Backend: FastAPI (`skill_server.py`)

```
GET  /api/skills                         list all skills with last eval data
GET  /api/skills/{name}                  skill content + history + eval metrics
POST /api/skills/{name}                  update skill content
GET  /api/leaderboard                    aggregated eval results, sorted by delta
POST /api/eval/run                       trigger eval (Server-Sent Events for live output)
GET  /api/trajectories                   query trajectory data
POST /api/skills/detect                  route a message to a skill
GET  /api/skills/{name}/history          git log for a skill
```

#### Frontend: Next.js + shadcn/ui + Tailwind

```
/                    Leaderboard (sortable table, delta sparklines, pass/warn/block badges)
/skills              Skill Library (pyramid view: atomic/concrete/abstract tabs)
/skills/[name]       Skill detail (Monaco editor, eval history chart, git history, Langfuse link)
/eval                Eval runner (select skill + trials → live SSE streaming output)
/observability       Embedded Langfuse iframe or deep-link to traces
```

#### Key UI components

**Leaderboard page:**
- Sortable table: skill name / weighted Δ / regression rate / last eval date / verdict badge
- Click row → skill detail page
- "Run all evals" button

**Skill detail page:**
- Monaco code editor for SKILL.md (with YAML frontmatter validation)
- Eval history: line chart of weighted delta over time
- Git history: list of commits with diffs
- Last Langfuse trace link
- "Run eval" button → SSE stream to live output panel

**Eval runner page:**
- Skill selector + trial count + condition selector
- Live streaming output (SSE) showing tasks as they complete
- Final verdict with gate tier

---

### Phase 4: Skill Portability — /commands and API (Week 5-6)

**Goal:** Skills can be loaded as /commands in Claude Code and invoked via REST from any agent system.

#### 4.1 Skill Loader (common layer)

`eval/skill_loader.py` (spec above in Phase 1) becomes the shared runtime. Any integration calls `load_skill(path)` and gets a `LoadedSkill` with `body` (ready to inject), `description` (for routing), and metadata.

#### 4.2 Claude Code /command export

```bash
# Export all skills to Claude Code format
python -m eval.export_skill --all --target ~/.claude/skills/

# In Claude Code session after export:
/flight-search find flights JFK to LAX July 10
/booking-skill book FL123 for Alice Johnson
/planning-skill plan 4-day trip to Tokyo in August
```

Export format: each skill becomes a directory under `~/.claude/skills/` with `skill.md` (renamed from SKILL.md) and `metadata.json`.

#### 4.3 Skill API server

```python
# skill_server.py
POST /skills/{name}/invoke    # run skill against a user message
GET  /skills                  # list all skills with descriptions
POST /skills/detect           # detect which skill a message needs
```

Any downstream system (voice agent, chat UI, automation) can call this API without knowing the LangGraph implementation details.

#### 4.4 Registry integration (agentskills.io)

```bash
python -m eval.registry push --skill flight-search --version 0.1.0
python -m eval.registry pull --skill travel/hotel-search
```

---

### Phase 6: Dynamic Skill Creation (Week 7-8)

**Goal:** Skills can be created without a human writing SKILL.md from scratch. Two paths: a CLI command that drafts content via LLM, and an automated pipeline that proposes new skills from clustered eval failures.

#### 6.1 `skills generate` CLI command

A new `generate` command that calls an LLM to draft a full SKILL.md given a plain-English description, then scaffolds and registers it exactly like `skills create`.

```bash
skills generate "Handle flight disruptions, rebooking on cancelled flights, \
  and compensation claims" \
  --name disruption-handling \
  --owner travel-platform
# → drafts SKILL.md via LLM
# → writes skills/disruption-handling/SKILL.md
# → registers in registry.yaml
# Output: "Created skill: skills/disruption-handling  (draft — review before opening PR)"
```

Implementation in `src/travel_agent_skills/commands/generate.py`:

```python
def generate_skill(
    *,
    name: str,
    description: str,
    owners: list[str],
    model: str = "claude-haiku-4-5-20251001",
    project_root: Path | None = None,
) -> Path:
    """Draft a SKILL.md body via LLM, scaffold the skill dir, register in registry."""
    validate_skill_name(name)
    root = project_root or Path.cwd()
    prompt = GENERATE_PROMPT.format(name=name, description=description)
    body = call_llm(prompt, model=model)          # returns markdown body only
    frontmatter = build_frontmatter(name, description, owners[0])
    skill_content = f"{frontmatter}\n\n{body}"
    skill_dir = root / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(skill_content)
    upsert_skill_entry(root / "registry.yaml", name, SkillRegistryEntry(...))
    return skill_dir
```

The LLM prompt instructs the model to produce:
- A numbered workflow with `**Confirm required inputs**` as step 1
- A required inputs table, optional inputs table
- An output spec
- Edge cases and quality checks

The generated skill is always status `draft`. The human reviews it, edits as needed, then opens a PR. The eval gate runs as normal.

#### 6.2 Automated skill proposal from eval failures (GRPO → PR)

The eval platform's GRPO optimizer (`eval/optimizer/`) already clusters failed tasks and proposes skill improvements. Extend this pipeline to propose *new* skills when a task cluster has no matching skill at all.

**Flow:**

```
1. GRPO optimizer clusters failed eval tasks by domain + failure mode
2. For clusters where no skill exists → call LLM to draft SKILL.md body
3. Write draft to travel-agent-skills/skills/<proposed-name>/SKILL.md via GitHub API
4. Open a PR with title "proposal: auto-generated <name> skill"
5. CI eval gate runs automatically on the PR
6. Human reviews: edit content, approve or close PR
```

**New file in skill-testing-playground:** `eval/optimizer/propose_skill.py`

```python
def propose_skill_pr(
    cluster: FailureCluster,
    github_token: str,
    repo: str = "Tabhi-Commons/travel-agent-skills",
) -> str:
    """Draft a new skill from a failure cluster and open a PR. Returns PR URL."""
    skill_name = cluster.suggested_skill_name   # e.g. "disruption-handling"
    body = draft_skill_body(cluster)            # LLM call
    frontmatter = build_frontmatter(skill_name, cluster.description)
    content = f"{frontmatter}\n\n{body}"
    pr_url = open_skill_pr(
        repo=repo,
        skill_name=skill_name,
        skill_content=content,
        token=github_token,
        title=f"proposal: auto-generated {skill_name} skill",
        body=f"Auto-proposed from {len(cluster.tasks)} failed eval tasks "
             f"in domain `{cluster.domain}`. Review and edit before merging.",
    )
    return pr_url
```

**Safeguards:**
- Proposed skills are always `draft` status
- PR title is prefixed `proposal:` so it is visually distinct
- Eval gate must PASS before the PR can merge — a bad auto-generated skill cannot slip through
- The optimizer never auto-merges — a human approves every PR

---

### Phase 5: Multi-model Eval + Gate Calibration (Week 7+)

**Goal:** Test skills across multiple models (Gemini 2.5 Flash, GPT-4.1-mini, Claude Haiku) to find model-skill compatibility gaps.

- Add `--model` flag to `ab_compare.py`
- Leaderboard shows per-model delta columns
- Gate thresholds calibrated against production outcomes (connect eval delta to real booking conversion data)

---

## Skill Gaps to Fill

| Skill needed | Domain | Priority | Status |
|-------------|--------|----------|--------|
| `hotel-search` | hotel_search | High — 10 tasks | ✅ created |
| `fare-rules` | fare_rules | High — 6 tasks | ✅ created |
| `modify-booking` | edge_cases | Medium — 6 tasks | ✅ created |
| `disruption-handling` | disruption | Low — not yet in task bank | ❌ missing |

`disruption-handling` is a candidate for Phase 6 auto-generation from eval failure clusters.

---

## Task Bank Alignment

| task.toml skill | travel-agent-skills skill | Status |
|----------------|--------------------------|--------|
| `flight-search` | `flight-search` | ✅ aligned |
| `booking-skill` | `booking-skill` | ✅ aligned (was `book-itinerary`, remapped) |
| `hotel-search` | `hotel-search` | ✅ aligned |
| `fare-rules` | `fare-rules` | ✅ aligned |
| `modify-booking` | `modify-booking` | ✅ aligned |
| `ancillery` | `ancillery-skill` | ⚠️ no tasks in bank yet |

---

## Data Flow End-to-End

```
1. Engineer authors skill in travel-agent-skills
   └── skills create hotel-search --owner travel-platform

2. Opens PR to skills/hotel-search/SKILL.md

3. GitHub Actions triggers in travel-agent-skills
   └── skills validate --all (format check)
   └── checkout skill-testing-playground
   └── python -m eval.ab_compare --skill-path skills/hotel-search --trials 5

4. Eval runs: 10 hotel-search tasks × 5 trials each
   ├── no_skill condition (baseline)
   └── with_skill condition (hotel-search skill injected)

5. Gate check produces verdict
   ├── T1 BLOCK: weighted delta < -0.05 OR any booking task regressed > 15%
   ├── T2 SOFT BLOCK: negative delta or regression rate > 20%
   ├── T3 WARN: small regressions, overall positive
   └── PASS: weighted delta ≥ +0.05, regression rate < 20%

6. Result posted to PR as comment with:
   - Weighted delta (+0.XXX)
   - Regression rate (X%)
   - Verdict badge
   - Langfuse trace link for each regressed task

7. On merge: skill packaged as ZIP, leaderboard updated
```

---

## Commit and Branch Policy

- All commits in plain imperative style: `feat:`, `fix:`, `docs:`, `chore:`
- No co-author attribution lines
- Every task in a plan gets its own commit
- Skill changes get evaluated before merge — never commit unevaluated skills to main

---

## Open Questions

1. **Langfuse hosting** — self-host via Docker Compose or use langfuse.com free tier for now?
2. **Who triggers evals** — GitHub Actions only, or also support local dev: `skills eval flight-search`?
3. **disruption-handling skill** — author manually or use Phase 6 auto-generation as the first live test of that pipeline?
4. **`skills generate` LLM model** — use Claude Haiku for cost, or Sonnet for quality? Should output go through `skills validate` automatically before writing to disk?
5. **GRPO propose threshold** — how many failed tasks in a cluster before a skill proposal is auto-opened? Suggested default: 5+ failures in same domain with no matching skill.

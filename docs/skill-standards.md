# Skill Standards

This project stores shared skills that multiple teams and projects can consume. Keep every skill portable, versioned, auditable, and easy to validate.

## Naming Convention

Skill names must follow the open Agent Skills name rules:

- Use lowercase letters, numbers, and hyphens only.
- Do not start or end with a hyphen.
- Do not use consecutive hyphens.
- Keep names under 64 characters.
- Make the folder name exactly match the `name` field in `SKILL.md`.

Prefer short, action-oriented names:

- `flight-search`
- `hotel-search`
- `itinerary-planning`
- `booking-policy-review`

Avoid vague names:

- `travel`
- `helper`
- `agent-utils`

## `SKILL.md` Frontmatter

Each skill must include the required open Agent Skills frontmatter fields:

```yaml
---
name: flight-search
description: Search, compare, and summarize flight options using approved flight data sources. Use when users ask for airfare, routes, flight availability, airline comparisons, layovers, cabin classes, baggage-aware options, or travel flight recommendations.
license: Apache-2.0
metadata:
  author: travel-platform
  version: "0.1.0"
---
```

Keep `SKILL.md` metadata portable. Good frontmatter metadata describes the skill package itself:

- `name`
- `description`
- `license`
- `metadata.author`
- `metadata.version`
- runtime requirements, if a skill needs them

Do not put repository workflow metadata in `SKILL.md`.

## Registry Metadata

Project governance metadata belongs in `registry.yaml`:

```yaml
skills:
  flight-search:
    path: skills/flight-search
    version: "0.1.0"
    owners:
      - travel-platform
    status: draft
    tags:
      - travel
      - flight
      - search
    distribution:
      - org-provisioned
      - zip
      - project-local
```

Use `registry.yaml` for:

- owners and maintainers
- lifecycle status
- discovery tags
- supported distribution channels
- release metadata references
- checksums or packaged artifact references

## Lifecycle Statuses

Use one of these statuses:

- `draft`: Skill is being authored and should not be treated as stable.
- `review`: Skill is ready for team review and validation.
- `stable`: Skill is approved for downstream project consumption.
- `deprecated`: Skill remains available for compatibility but should not be adopted by new consumers.

## Versioning

Use semantic versioning:

- Patch versions for wording fixes that do not change behavior.
- Minor versions for backward-compatible workflow or resource additions.
- Major versions for breaking changes to instructions, required inputs, output formats, or bundled resource contracts.

## Distribution And Updates

Declare how a skill is intended to reach consumers:

- `org-provisioned`: Installed by an organization owner or admin for a managed workspace.
- `shared-workspace`: Shared with users or teams inside a managed workspace.
- `zip`: Packaged for manual upload by individual users or external customers.
- `project-local`: Copied into a project-level skills directory.

Use this update behavior guidance:

- Managed org or shared workspace channels can be centrally updated by the workspace owner/admin.
- Manual ZIP installs are private copies and require the user or customer to reinstall the newer ZIP.
- Project-local installs can be updated by pulling from the central repository or copying a newer packaged skill.

Packaged releases should include install provenance so users can report the exact version they have installed.

## Skill Contents

Use the smallest useful skill structure:

```text
skill-name/
├── SKILL.md
├── references/
├── scripts/
└── assets/
```

Only add optional folders when the skill needs them:

- `scripts/`: executable code agents can run
- `references/`: documentation agents can load on demand
- `assets/`: static templates, schemas, lookup files, or media

Do not add `references/`, `scripts/`, or `assets/` just because they are available.

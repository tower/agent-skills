# Tower Agent Skills

Agent skills for building on [Tower](https://tower.dev) — installable into Claude Code, Cursor, and other agents via the [`skills`](https://github.com/vercel-labs/skills) CLI.

## Installation

Install all skills from this repository:

```bash
npx skills add tower/agent-skills
```

Install a specific skill:

```bash
npx skills add tower/agent-skills --skill tower-ingest
```

Target a specific agent:

```bash
npx skills add tower/agent-skills -a claude-code
```

List available skills without installing:

```bash
npx skills add tower/agent-skills --list
```

## Skills

| Skill | Description |
|---|---|
| [`tower-ingest`](skills/tower-ingest/SKILL.md) | Author, test, deploy, and schedule data ingestion pipelines on Tower that land external data (APIs, databases, SaaS tools, files) into a Tower-managed Apache Iceberg lakehouse. |
| [`tower-analyze`](skills/tower-analyze/SKILL.md) | Analyze data in the Tower lakehouse. |

## Repository layout

Each skill lives in its own directory under `skills/`, with a `SKILL.md` containing YAML frontmatter (`name`, `description`) followed by the skill instructions:

```
skills/
├── tower-ingest/
│   └── SKILL.md
└── tower-analyze/
    └── SKILL.md
```

## Adding a new skill

1. Create `skills/<skill-name>/SKILL.md`.
2. Add frontmatter with a unique `name` (lowercase, hyphens) and a `description` that tells the agent when to use the skill.
3. Write the skill instructions in markdown below the frontmatter.
4. Add a row to the Skills table above.

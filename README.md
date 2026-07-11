<p align="center">
  <br>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/tower-logo-light.png">
    <img src="assets/tower-logo-dark.png" alt="Tower" width="280">
  </picture>
  <br><br>
</p>

# Make every agent a data agent

[![Validate skills](https://github.com/tower/agent-skills/actions/workflows/test.yml/badge.svg)](https://github.com/tower/agent-skills/actions/workflows/test.yml)

Open-source [Agent Skills](https://github.com/vercel-labs/skills) that teach AI agents (Claude Code, Cursor, and other skills-compatible agents) how to do useful data work with [Tower](https://tower.dev): ingest enterprise data into a governed, open lakehouse built on Apache Iceberg, and delegate access to your team with Tower securely. 

```bash
npx skills add tower/agent-skills
```

## The skills

| Skill | What it does |
|---|---|
| [`tower-ingest`](skills/tower-ingest/SKILL.md) | Gets data **into** the lakehouse. Builds ingestion pipelines that land raw data from APIs, databases, SaaS tools, and files into Iceberg tables, then deploys and schedules them on Tower's managed compute. Credentials live in Tower secrets and never in code, config, or chat. |
| [`tower-data`](skills/tower-data/SKILL.md) | Gets answers **out** of the lakehouse. Vends a short-lived, read-only credential, attaches the Iceberg catalog in [DuckDB](https://duckdb.org), and answers questions with SQL you can audit. The agent never touches the source systems. |

Together they cover the full loop: source → governed lakehouse → answer. Tower sits in the middle, so every run has a status, history, and logs, and access is scoped and auditable.

## Getting started

You'll need a [Tower account](https://tower.dev) and the CLI:

```bash
pip install tower
tower login
npx skills add tower/agent-skills
```

Then ask your agent for what you want — "get our Stripe data into the lakehouse," "how many teams ran apps last week?" — and the right skill takes it from there.

Useful variants:

```bash
npx skills add tower/agent-skills --skill tower-data   # just one skill
npx skills add tower/agent-skills -a claude-code       # target a specific agent
npx skills add tower/agent-skills --list               # see what's here first
```

## Contributing

Issues and pull requests are welcome. These skills are meant to improve through real use. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add a skill and [AGENTS.md](AGENTS.md) for the design principles every data skill here follows.

## Learn more

- [Learn more about Tower](https://tower.dev)
- [Tower documentation](https://docs.tower.dev)
- [Make Every Agent a Data Agent](https://tower.dev/blog/make-every-agent-a-data-agent) — the announcement post

## License

[MIT](LICENSE)

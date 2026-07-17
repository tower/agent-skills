---
name: tower-data
description: Query and analyze data in a Tower-managed Apache Iceberg lakehouse using the Tower CLI's built-in read-only SQL query command (`tower catalogs query`). Use this skill whenever the user asks a question about their company or business data (revenue, customers, orders, metrics, KPIs, trends), asks to explore, query, or analyze tables, mentions their lakehouse, Iceberg catalog, or Tower data — even if they don't mention SQL, DuckDB, or Tower explicitly. Also use it when asked "what data do we have?" or to build a report or summary from company data.
---

# Tower Data Analysis

Tower manages Apache Iceberg lakehouses. This skill lets you answer questions about the user's business data with `tower catalogs query`, which vends short-lived read-only credentials and runs SQL through DuckDB in a single command — no credential handling on your side.

**Core loop: discover tables with `tower catalogs show` → query with `tower catalogs query` → answer in plain language.**

## Fast path (use this)

```bash
# Discover tables (schemas + table names, no credentials needed)
tower catalogs show default

# Run SQL — read-only by default; add -j for JSON output
tower catalogs query default --sql 'SELECT * FROM "default".bronze.users LIMIT 10'

# Longer SQL via stdin
tower catalogs query default < analysis.sql

# Non-default catalog/environment
tower catalogs query my-catalog --environment production --sql '...'
```

Reference tables as `<catalog>.<namespace>.<table>` — the catalog name usually needs quoting since `default` is a SQL keyword: `"default".gold.revenue`.

Each invocation vends fresh short-lived credentials internally, so token expiry and shell-state loss between commands are non-issues. Credentials never appear in output — nothing to redact.

Batch related statements into one invocation where possible (each call pays a credential-vend + attach cost of a couple seconds). For multi-pass analysis over the same big table, `CREATE TEMP TABLE t AS SELECT <cols> FROM ...` at the top of the batch, then query the temp table — repeated scans of Iceberg tables are slow.

## Before you query: check for saved semantics

Business questions often have team-specific definitions (e.g. which users count as "internal", how "active" is defined) that are not derivable from schemas. Check agent memory / prior analyses for saved definitions before inventing a filter, and when the user confirms a definition, save it for next time.

## Security rules (non-negotiable)

1. **Queries are read-only by default.** Never pass `--write` unless the user explicitly asks to write data, and confirm with them first.
2. **Never print, log, or echo credentials.** `tower catalogs query` keeps them internal; if you fall back to manual vending (below), the token stays in an environment variable and never enters your response, a file, or a code comment.
3. Treat query *results* as the user's private business data: use them to answer the question, don't republish them elsewhere.

## Prerequisites

Check that the Tower CLI is installed, recent enough, and authenticated:

```bash
tower version          # needs a version with `tower catalogs query` (0.3.70+)
tower teams list       # verifies auth
```

- If the command isn't found: install with `pip install tower` (or `uvx tower ...` per invocation).
- If `tower catalogs query` doesn't exist: `pip install --upgrade tower`, or use the DuckDB fallback below.
- If it errors with an authentication problem: ask the user to run `tower login` (it opens a browser; you can't complete it for them).

## Step 1: Pick the catalog

Most teams have one catalog. List what's available:

```bash
tower catalogs list
```

- If a catalog named `default` exists (Tower's managed lakehouse), use it.
- If exactly one catalog exists, use that one.
- If several exist and the user hasn't specified, show them the list and ask which one — don't guess.

Note the catalog's **environment** — pass `--environment` on subsequent commands if it isn't `default`.

## Step 2: Discover before you query

Never assume table names or schemas. `tower catalogs show <name>` lists every schema and table in the catalog without vending credentials:

```bash
tower catalogs show default            # add -j for JSON
```

Then inspect the columns of the tables you plan to use:

```bash
tower catalogs query default --sql 'DESCRIBE "default".gold.<table>'
```

Many Tower lakehouses follow a medallion layout (`bronze` = raw, `silver` = cleaned, `gold` = business-ready aggregates). **Prefer gold-layer tables for business questions**; fall back to silver, and only use bronze when nothing else has the data.

Before aggregating, sanity-check grain and freshness:

```bash
tower catalogs query default --sql 'SELECT COUNT(*), MIN(<date_col>), MAX(<date_col>) FROM "default".gold.<table>'
```

## Step 3: Query and answer

- Qualify table names fully: `"<catalog>".<namespace>.<table>`.
- Add `LIMIT` to exploratory queries; only run full aggregations once you understand the table.
- Use `-j`/`--json` when you need to post-process results programmatically.
- Answer the user's question in plain language first, with the numbers. Include the SQL you ran (in a code block) so the result is auditable.
- If a result looks surprising (empty, wildly large, stale `MAX(date)`), say so rather than presenting it as fact, and check an adjacent table before concluding.

## Fallback: manual DuckDB session

Use this only when `tower catalogs query` is unavailable (old CLI) or you need a persistent interactive DuckDB session. `query.sh` in this skill's directory does vend → attach → execute in one shot; SQL goes in on stdin and the catalog is attached as `lakehouse`:

```bash
echo "SHOW ALL TABLES;" | <skill-dir>/query.sh              # catalog=default, env=default
<skill-dir>/query.sh my-catalog production < analysis.sql   # explicit catalog + environment
```

Under the hood it runs `tower --json catalogs credentials <CATALOG> --environment <ENV> --mode read`, exports the OAuth token as `TOWER_CATALOG_TOKEN` (never printed), and attaches the warehouse in DuckDB via an Iceberg secret. If you must replicate this manually, keep the token in the environment variable, pass it into DuckDB with `getenv`, and never leave it on disk. `tower catalogs credentials <CATALOG> --format duckdb` prints a ready-made connection snippet (formats: `duckdb`, `pyiceberg`, `spark`, `dbt`, `all`).

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `unrecognized subcommand 'query'` | Old CLI | `pip install --upgrade tower`, or use `query.sh` fallback |
| Auth error / prompted to log in | Session expired | User runs `tower login` |
| `Failed to vend credentials ... Not found` | No Tower-managed catalog, or wrong `--environment` | Check `tower catalogs list`; catalog creation is UI-only |
| Table not found | Wrong namespace or unquoted catalog name | Re-run `tower catalogs show`; quote the catalog: `"default".ns.table` |
| Query killed / very slow | Heavy repeated scans of Iceberg tables | Materialize a temp table first, split the batch |
| Write statement rejected | Expected — queries are read-only | Confirm intent with the user, then re-run with `--write` |

## What this skill is not for

- **Writing or ingesting data** — that's `tower-integration` (pipelines, secrets, schedules). Don't reach for `--write` to land data; write paths belong in a deployed app.
- Building, deploying, or scheduling Tower apps — the builder workflow (Towerfile, `tower deploy`, `tower run`) lives in `tower-integration` / the base `tower` skill. If the user wants to *productionize* an analysis as a recurring job, hand off there.

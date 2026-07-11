---
name: tower-ingest
description: Author, test, deploy, and schedule data ingestion pipelines on Tower that land external data (APIs, databases, SaaS tools, files) into a Tower-managed Apache Iceberg lakehouse. Use this skill whenever the user wants to ingest, load, sync, extract, or import data into their lakehouse or Tower, mentions dlt/dltHub, connectors, ELT/ETL, or says things like "get our Stripe/Postgres/GitHub/Shopify data into Tower", "build a pipeline", or "keep this data up to date" — even if they don't say "ingestion" explicitly. Covers Tower apps, Towerfiles, parameters, secrets, environments, catalogs, tables, schedules, retries, and multi-app orchestration.
---

# Tower Ingestion Authoring

Build ingestion pipelines as Tower apps: Python (preferably dlt) extracts from a source and lands data in Iceberg tables in the team's Tower-managed catalog. Test locally, deploy, schedule, verify.

**Core loop: clarify source → scaffold app → resolve secrets WITH the user → write pipeline → run local → deploy → schedule → verify data landed.**

## Principles

1. **Secrets never appear in code, Towerfiles, or chat.** Credentials live in Tower secrets, injected as environment variables at runtime. Follow the Secrets Protocol below — do not write code that needs a credential before the secret exists.
2. **Idempotent by default.** Every pipeline must be safe to re-run: use merge/upsert write modes or explicit deduplication. Schedules retry; design for it.
3. **Land raw data in a `bronze` namespace** (e.g. `bronze.stripe_invoices`). Transformations to silver/gold are a separate app (dbt or Polars), not the ingestion app's job.
4. **Never edit Towerfile TOML by hand.** Use the Tower MCP tools (`tower_file_generate`, `tower_file_update`, `tower_file_add_parameter`, `tower_file_validate`) or CLI equivalents.
5. **Discover, don't assume.** Check what catalogs, secrets, and apps already exist before creating new ones.

## Prerequisites

```bash
tower teams list        # verifies install + auth
tower catalogs list     # confirm the target catalog (usually `default`, Tower-managed)
tower secrets list      # see which secrets already exist (previews only)
tower apps list         # avoid duplicate app names
```

If the CLI is missing: `pip install tower`. If unauthenticated: the user must run `tower login` (opens a browser). If Tower MCP tools (`tower_*`) are available, prefer them over raw CLI.

## Step 1: Clarify the job

Confirm with the user before writing code:
- **Source**: what system, and does a [dlt verified source](https://dlthub.com/docs/dlt-ecosystem/verified-sources/) exist for it? Prefer dlt verified sources (`sql_database`, `rest_api`, `github`, `stripe`, `hubspot`, `google_sheets`, `filesystem`, ...) over hand-rolled clients.
- **Tables and volume**: which entities, roughly how many rows, full refresh or incremental?
- **Cadence**: one-off backfill, hourly, daily?
- **Write mode**: append (event/log data), merge/upsert (entities with a primary key — the default), or replace (small reference tables).

## Step 2: Scaffold the app

```bash
mkdir <app-name> && cd <app-name> && uv init
```

Keep `pyproject.toml` minimal — `[project]` metadata and dependencies only (e.g. `dlt`, `pyarrow`, `tower`). No `[build-system]` sections. Also write a `requirements.txt` mirroring the dependencies (Tower installs from it at runtime).

Then generate and configure the Towerfile:

```
tower_file_generate → tower_file_update (name, script, description, source globs)
→ tower_file_add_parameter (for runtime knobs) → tower_file_validate
```

Use **parameters** for non-secret runtime configuration the user may want to vary per run or per schedule: date ranges for backfills, table lists, write mode. Access in code with `tower.parameter("name")`. Use **hidden parameters** (`hidden=true`, no default) only for sensitive values that vary per invocation; standing credentials belong in secrets, not parameters.

Naming convention: `ingest-<source>` (e.g. `ingest-stripe`, `ingest-github`).

## Step 3: Secrets Protocol (do not skip)

Before writing pipeline code, enumerate every credential the source needs (API key, DB connection string, OAuth token). Then **stop and prompt the user**:

1. Tell them exactly which secrets are needed, what each is for, and where to obtain it (e.g. "a Stripe restricted API key with read access to invoices, from the Stripe dashboard → Developers → API keys").
2. Name secrets using **dlt's environment-variable convention** so dlt picks them up with zero glue code — Tower injects secrets as environment variables at runtime and integrates with dlt's config system. Examples:
   - `SOURCES__SQL_DATABASE__CREDENTIALS` — database connection string
   - `SOURCES__GITHUB__ACCESS_TOKEN`
   - `SOURCES__STRIPE_ANALYTICS__STRIPE_SECRET_KEY`
3. Give the user the exact command **to run themselves in their own terminal**, so the value never enters this conversation:

```bash
tower secrets create --name=SOURCES__GITHUB__ACCESS_TOKEN --value='<paste value here>'
```

   Add `--environment=production` if the secret is environment-specific; secrets created in `default` are inherited by all environments and can be overridden per environment.
4. If the user pastes a secret value into the chat instead, create the secret immediately (via `tower_secrets_create` or CLI), confirm creation, and advise them to rotate the credential since it has now transited a conversation. Never repeat the value back.
5. Verify with `tower secrets list` (shows previews only) before proceeding.

For local testing, `tower run --local` fetches Tower secrets into the local run — no `.env` files, no `secrets.toml`. Do not create local credential files.

## Step 4: Write the pipeline

Preferred pattern — **dlt extracts, Tower tables land the data in Iceberg**:

```python
import dlt, tower, pyarrow as pa

def main():
    # 1. Extract with dlt (credentials arrive via env vars from Tower secrets)
    source = ...  # dlt verified source, e.g. github(), sql_database(), rest_api(...)

    # 2. Land each resource as Arrow into the Tower-managed catalog
    for resource_name, batches in extract_as_arrow(source):  # dlt supports arrow extraction
        table = tower.tables(f"{resource_name}", namespace="bronze") \
                     .create_if_not_exists(schema_of(batches))
        table.upsert(batches, join_cols=[...])   # idempotent; use insert() for append-only

if __name__ == "__main__":
    main()
```

Key SDK facts:
- `tower.tables('name', catalog='slug')` — omit `catalog` when the catalog slug is `default` (the Tower-managed lakehouse).
- Methods: `create_if_not_exists(schema)`, `create(schema)`, `load()`, `insert()`, `upsert()`, `delete()`, `read()`, `to_polars()`. Schemas are PyArrow schemas.
- `tower.parameter("name")` for parameters; `tower.info.environment()` / `TOWER_ENVIRONMENT` to branch on environment.

Alternative pattern: if the team standardizes on a dlt destination directly (e.g. Iceberg-capable destination configured against the Tower catalog), that's acceptable — but the tower.tables path is the supported default and keeps the catalog integration automatic.

Incremental loads: persist a cursor (e.g. `max(updated_at)` read from the target table via `to_polars()`) rather than relying on local state — runners are ephemeral and runs must be stateless.

## Step 5: Test locally

```
tower_run_local
```

This installs the app's dependencies, injects Tower secrets, and runs on the user's machine — the closest thing to production. Iterate here until clean. Check row counts in the output logs.

## Step 6: Deploy and run in the cloud

```
tower_apps_create → tower_deploy → tower_run_remote
```

Then confirm the run exited cleanly:

```
tower_apps_show <app>       # recent runs and statuses
tower_apps_logs <app>#<n>   # logs for a specific run
```

Run status meanings: `exited` = success; `crashed` = your code failed (non-zero exit); `errored` = infrastructure failure; `retrying` = a retry policy is in effect. Time in `starting` is cold-start, not your code. Configure a retry policy for scheduled ingestion so transient source/API failures self-heal.

Environments: iterate against `default`; when stable, promote with `tower deploy --environment=production` (or promote an existing version in the UI). Override environment-specific secrets (e.g. prod vs staging DB) by creating same-named secrets in that environment.

## Step 7: Schedule

```bash
tower schedules create --app=ingest-<source> --cron="0 6 * * *"
tower schedules create --app=ingest-<source> --cron="0 6 * * *" --parameter=TABLES="invoices,customers"
```

(MCP: `tower_schedules_create` / `list` / `update` / `delete`.) Choose a cadence matching the user's answer in Step 1. For multi-source loads, either one schedule per app, or an orchestrator app that fans out with `tower.run()` and `tower.wait()` and runs on a single schedule.

## Step 8: Verify the data landed

Close the loop — never declare success from logs alone. Read the target table back:

```python
import tower
df = tower.tables("bronze.<table>").to_polars().collect()
print(df.height, df.select("<timestamp_col>").max())
```

Or hand off to the **tower-data** skill (vend read credentials, query with DuckDB) to run row-count and freshness checks and show the user actual rows. Offer this explicitly: "want me to query it to confirm?"

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| dlt can't find credentials | Secret name doesn't match dlt's env-var convention | Rename secret (Step 3 naming); `tower secrets list` to check |
| Works locally, `crashed` in cloud | Missing dependency in `requirements.txt`, or secret only exists locally/in another environment | Pin deps; check `tower secrets list -a` |
| Duplicate rows after re-run | Append mode without dedup | Switch to `upsert()` with join columns |
| Run stuck in `pending` | Self-hosted runner mode enabled but no runner online | Check Settings → Self-Hosted Runners, or start a runner |
| Table not visible to analysts | Wrong namespace/catalog | Confirm `bronze` namespace in the `default` catalog |
| Schedule ran, no new data | Cursor logic wrong or source-side lag | Log the cursor value each run; check source freshness |

## What this skill is not for

Querying or analyzing the lakehouse — that's **tower-data** (read-only credentials + DuckDB). Building transformations (bronze → silver/gold) — author a separate dbt or Polars app with the base **tower** skill. General app deployment without data landing — base **tower** skill.

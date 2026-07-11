---
name: tower-data
description: Query and analyze data in a Tower-managed Apache Iceberg lakehouse using DuckDB and short-lived, read-only credentials vended by the Tower CLI. Use this skill whenever the user asks a question about their company or business data (revenue, customers, orders, metrics, KPIs, trends), asks to explore, query, or analyze tables, mentions their lakehouse, Iceberg catalog, or Tower data — even if they don't mention SQL, DuckDB, or Tower explicitly. Also use it when asked "what data do we have?" or to build a report or summary from company data.
---

# Tower Data Analysis

Tower manages Apache Iceberg lakehouses. This skill lets you answer questions about the user's business data by vending short-lived, scoped credentials from Tower and querying the lakehouse locally with DuckDB.

**Core loop: vend read-only credentials → attach the catalog in DuckDB → discover tables → query → answer in plain language.**

## Security rules (non-negotiable)

1. **Default to read-only.** Always vend credentials with `--mode read`. Only use `--mode read-write` if the user explicitly asks to write data, and confirm with them first.
2. **Never print, log, or echo the OAuth token.** Keep it in the `TOWER_CATALOG_TOKEN` environment variable or pass it into DuckDB via a secret. Never paste it into your response, a file the user will read, or a code comment.
3. **Tokens are short-lived.** If a query fails with an auth error (401/403) partway through a session, re-vend credentials and retry — don't ask the user to debug.
4. Treat query *results* as the user's private business data: use them to answer the question, don't republish them elsewhere.

## Prerequisites

Check that the Tower CLI is installed and authenticated:

```bash
tower teams list
```

- If the command isn't found: install with `pip install tower` (or `uvx tower ...` per invocation).
- If it errors with an authentication problem: ask the user to run `tower login` (it opens a browser; you can't complete it for them).

## Step 1: Pick the catalog

Most teams have one catalog. List what's available:

```bash
tower catalogs list
```

- If a catalog named `default` exists (Tower's managed lakehouse), use it.
- If exactly one catalog exists, use that one.
- If several exist and the user hasn't specified, show them the list and ask which one — don't guess.

`tower catalogs show <name>` displays the catalog's type, environment, and property names if you need more detail. Note the **environment** — pass it explicitly in the next step if it isn't `default`.

## Step 2: Vend short-lived read credentials

```bash
export TOWER_CATALOG_TOKEN="$(tower --json catalogs credentials <CATALOG> --environment <ENV> --mode read | python3 -c 'import json,sys; print(json.load(sys.stdin)["credentials"]["oauth_token"])')"
```

Also capture the connection details (safe to display — they contain no secret):

```bash
tower --json catalogs credentials <CATALOG> --environment <ENV> --mode read | python3 -c 'import json,sys; c=json.load(sys.stdin)["credentials"]; print(c["catalog_uri"]); print(c["warehouse"]); print(c["expires_at"])'
```

The JSON `credentials` object contains: `catalog_uri` (Iceberg REST endpoint), `warehouse`, `oauth_token`, `mode`, and `expires_at`. Note `expires_at` — for a long analysis session, re-vend before it lapses.

Tip: `tower catalogs credentials <CATALOG> --format duckdb` prints a ready-made connection snippet (formats: `duckdb`, `pyiceberg`, `spark`, `dbt`, `all`). You can use it directly, but prefer the explicit setup below so the region is correct.

## Step 3: Attach the catalog in DuckDB

Substitute `<WAREHOUSE>`, `<CATALOG_URI>` from step 2. Set `s3_region` to the region the lakehouse lives in (Tower-hosted defaults to `eu-central-1`; ask or check `tower catalogs show` if unsure).

```bash
duckdb lakehouse.duckdb <<'SQL'
INSTALL httpfs; LOAD httpfs;
INSTALL iceberg; LOAD iceberg;
SET s3_region='eu-central-1';
CREATE OR REPLACE SECRET tower_cat (TYPE iceberg, TOKEN getenv('TOWER_CATALOG_TOKEN'));
ATTACH '<WAREHOUSE>' AS lakehouse (TYPE iceberg, SECRET tower_cat, ENDPOINT '<CATALOG_URI>', DEFAULT_REGION 'eu-central-1');
SQL
```

If `getenv` is unavailable in the installed DuckDB version, generate the SQL file from a script that reads `$TOWER_CATALOG_TOKEN` and interpolates it, run it, then delete the file. Never leave the token on disk.

If DuckDB isn't installed: `curl https://install.duckdb.org | sh` or `pip install duckdb` and use the Python API with the same statements.

## Step 4: Discover before you query

Never assume table names or schemas. Discover first:

```sql
SHOW ALL TABLES;
-- or
SELECT table_schema, table_name FROM information_schema.tables WHERE table_catalog = 'lakehouse';
DESCRIBE lakehouse.<namespace>.<table>;
```

Many Tower lakehouses follow a medallion layout (`bronze` = raw, `silver` = cleaned, `gold` = business-ready aggregates). **Prefer gold-layer tables for business questions**; fall back to silver, and only use bronze when nothing else has the data.

Before aggregating, sanity-check grain and freshness:

```sql
SELECT COUNT(*), MIN(<date_col>), MAX(<date_col>) FROM lakehouse.gold.<table>;
```

## Step 5: Query and answer

- Qualify table names fully: `lakehouse.<namespace>.<table>`.
- Add `LIMIT` to exploratory queries; only run full aggregations once you understand the table.
- Answer the user's question in plain language first, with the numbers. Include the SQL you ran (in a code block) so the result is auditable — but never the token.
- If a result looks surprising (empty, wildly large, stale `MAX(date)`), say so rather than presenting it as fact, and check an adjacent table before concluding.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| 401/403 mid-session | Token expired | Re-vend (step 2), re-attach |
| `ATTACH` fails / HTTP error | Wrong endpoint or warehouse | Re-read values from step 2 JSON; check `--environment` |
| S3 access error on scan | Wrong region | Set `s3_region` / `DEFAULT_REGION` to the lakehouse region |
| Table not found | Wrong namespace | Re-run discovery (step 4); check spelling of namespace |
| `iceberg` extension missing | Old DuckDB | Upgrade DuckDB (needs a recent version with Iceberg REST + ATTACH support) |
| Write attempted in read mode | Expected — token is read-only | Confirm intent with user, then re-vend with `--mode read-write` |

## What this skill is not for

Building, deploying, or scheduling Tower apps — that's the `tower` skill (builder workflow: Towerfile, `tower deploy`, `tower run`). If the user wants to *productionize* an analysis as a recurring job, hand off to that skill.

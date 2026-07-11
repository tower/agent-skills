#!/usr/bin/env bash
# Run SQL (from stdin) against a Tower lakehouse in one shot:
# vend read-only credentials -> attach in DuckDB -> execute -> exit.
# The OAuth token stays in an environment variable; it is never printed
# or written to disk.
#
# Usage:
#   echo "SHOW ALL TABLES;" | ./query.sh [catalog] [environment]
#   ./query.sh < analysis.sql
#
# The catalog is attached as `lakehouse` (e.g. lakehouse.bronze.users).
set -euo pipefail

CATALOG="${1:-default}"
ENVIRONMENT="${2:-default}"

CREDS_JSON="$(tower --json catalogs credentials "$CATALOG" --environment "$ENVIRONMENT" --mode read)"

eval "$(printf '%s' "$CREDS_JSON" | python3 -c '
import json, shlex, sys
c = json.load(sys.stdin)["credentials"]
print("export TOWER_CATALOG_TOKEN=%s" % shlex.quote(c["oauth_token"]))
print("CATALOG_URI=%s" % shlex.quote(c["catalog_uri"]))
print("WAREHOUSE=%s" % shlex.quote(c["warehouse"]))
')"

# Infer the S3 region from the catalog URI; default to Tower-hosted region.
REGION="$(printf '%s' "$CATALOG_URI" | grep -oE '[a-z]+-[a-z]+-[0-9]+' | head -1 || true)"
REGION="${REGION:-eu-central-1}"

{
  cat <<EOF
INSTALL httpfs; LOAD httpfs;
INSTALL iceberg; LOAD iceberg;
SET s3_region='${REGION}';
CREATE OR REPLACE SECRET tower_cat (TYPE iceberg, TOKEN getenv('TOWER_CATALOG_TOKEN'));
ATTACH '${WAREHOUSE}' AS lakehouse (TYPE iceberg, SECRET tower_cat, ENDPOINT '${CATALOG_URI}', DEFAULT_REGION '${REGION}');
EOF
  cat
} | duckdb -batch

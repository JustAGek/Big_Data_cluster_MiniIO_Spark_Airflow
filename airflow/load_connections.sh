#!/usr/bin/env bash
set -eo pipefail

# load_connections.sh
# Idempotently creates Airflow connections for MinIO (S3), AWS, and Snowflake.
# Behavior:
#  - If IMPORT_CONN_JSON is "true", the script will try to import
#    /opt/airflow/airflow_connections.json using `airflow connections import`.
#  - Otherwise it will create connections from environment variables (or
#    reasonable defaults/placeholders).
#
# Environment variables (examples):
#  IMPORT_CONN_JSON=true
#  MINIO_CONN_ID=minio_default
#  MINIO_HOST=minio
#  MINIO_PORT=9000
#  MINIO_LOGIN=minioadmin
#  MINIO_PASSWORD=minioadmin
#
#  AWS_CONN_ID=aws_default
#  AWS_ACCESS_KEY_ID=...
#  AWS_SECRET_ACCESS_KEY=...
#
#  SNOWFLAKE_CONN_ID=snowflake_default
#  SNOWFLAKE_CONN_URI=snowflake://USER:PASS@ACCOUNT/DB/SCHEMA?warehouse=WH

set +u
IMPORT_JSON="${IMPORT_CONN_JSON:-false}"
set -u

if [ "$IMPORT_JSON" = "true" ]; then
  if [ -f "/opt/airflow/airflow_connections.json" ]; then
    echo "Importing connections from /opt/airflow/airflow_connections.json"
    airflow connections import /opt/airflow/airflow_connections.json || true
  else
    echo "IMPORT_CONN_JSON=true but /opt/airflow/airflow_connections.json not found, skipping import"
  fi
  exit 0
fi

# --- MinIO / S3 connection ---
MINIO_CONN_ID="${MINIO_CONN_ID:-minio_default}"
MINIO_HOST="${MINIO_HOST:-minio}"
MINIO_PORT="${MINIO_PORT:-9000}"
MINIO_LOGIN="${MINIO_LOGIN:-minioadmin}"
MINIO_PASSWORD="${MINIO_PASSWORD:-minioadmin}"
MINIO_EXTRA="{\"endpoint_url\":\"http://${MINIO_HOST}:${MINIO_PORT}\",\"aws_access_key_id\":\"${MINIO_LOGIN}\",\"aws_secret_access_key\":\"${MINIO_PASSWORD}\",\"region_name\":\"us-east-1\"}"

echo "Creating S3/MinIO connection ($MINIO_CONN_ID)"
airflow connections add "$MINIO_CONN_ID" \
  --conn-type 'aws' \
  --conn-host "$MINIO_HOST" \
  --conn-login "$MINIO_LOGIN" \
  --conn-password "$MINIO_PASSWORD" \
  --conn-port "$MINIO_PORT" \
  --conn-extra "$MINIO_EXTRA" || true

# --- AWS connection (optional, created only if env vars provided) ---
AWS_CONN_ID="${AWS_CONN_ID:-aws_default}"
AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}" 
AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}"

if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
  echo "Creating AWS connection ($AWS_CONN_ID)"
  airflow connections add "$AWS_CONN_ID" \
    --conn-type 'aws' \
    --conn-login "$AWS_ACCESS_KEY_ID" \
    --conn-password "$AWS_SECRET_ACCESS_KEY" || true
else
  echo "AWS credentials not supplied via env; skipping aws connection creation"
fi

# --- Snowflake connection ---
SNOWFLAKE_CONN_ID="${SNOWFLAKE_CONN_ID:-snowflake_default}"
SNOWFLAKE_CONN_URI="${SNOWFLAKE_CONN_URI:-}"

if [ -n "$SNOWFLAKE_CONN_URI" ]; then
  echo "Creating Snowflake connection from URI ($SNOWFLAKE_CONN_ID)"
  airflow connections add "$SNOWFLAKE_CONN_ID" --conn-uri "$SNOWFLAKE_CONN_URI" || true
else
  # Build URI from pieces (placeholders if not provided)
  SNOW_USER="${SNOW_USER:-YOUR_SNOWFLAKE_USER}"
  SNOW_PASS="${SNOW_PASS:-YOUR_SNOWFLAKE_PASSWORD}"
  SNOW_ACCOUNT="${SNOW_ACCOUNT:-YOUR_ACCOUNT}"
  SNOW_DATABASE="${SNOW_DATABASE:-YOUR_DATABASE}"
  SNOW_SCHEMA="${SNOW_SCHEMA:-PUBLIC}"
  SNOW_WAREHOUSE="${SNOW_WAREHOUSE:-YOUR_WAREHOUSE}"

  # NOTE: ACCOUNT may need region suffix e.g. 'abc-12345.us-east-1'
  CONN_URI="snowflake://${SNOW_USER}:${SNOW_PASS}@${SNOW_ACCOUNT}/${SNOW_DATABASE}/${SNOW_SCHEMA}?warehouse=${SNOW_WAREHOUSE}"
  echo "Creating Snowflake connection ($SNOWFLAKE_CONN_ID) using assembled URI"
  airflow connections add "$SNOWFLAKE_CONN_ID" --conn-uri "$CONN_URI" || true
fi

echo "Airflow connection setup complete."

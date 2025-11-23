# Overview

This repository provides a local development stack for a Spark + MinIO data pipeline orchestrated by Airflow.

## Project contents

- `dags/` — Airflow DAG definitions (including `spark_minio_processing_dag.py`).
- `spark/` — Docker build context and `Dockerfile` used for Spark master and workers.
- `spark-jobs/` — PySpark jobs (e.g., `process_data.py`).
- `include/` — helper scripts (e.g., `upload_test_data.py`).
- `docker-compose.yml` — unified compose to run MinIO, Spark, Postgres, and Airflow locally.
- `airflow/` — Dockerfile used to build the Airflow image for this stack.
- `start-services.sh` / `stop-services.sh` — convenience scripts to start/stop the stack.

# Deploy Your Project Locally

You can start the stack using either the convenience script or Docker Compose directly.

## Option 1: Using the convenience script (recommended)

```powershell
./start-services.sh
```

## Option 2: Using Docker Compose directly

Start the full local stack (MinIO, Spark, Postgres, Airflow) with the main Docker Compose file:

```powershell
docker-compose -f docker-compose.yml up -d
```

Or use the MinIO and Spark specific setup:

```powershell
docker-compose -f docker-compose.minio-spark.yml up -d
```

This will build and start the following services:

| Service                    | Status     | Port      | URL                             |
| -------------------------- | ---------- | --------- | ------------------------------- |
| **Airflow Webserver**      | ✅ Running | 8080      | http://localhost:8080           |
| **Airflow Scheduler**      | ✅ Running | -         | Internal                        |
| **MinIO (Object Storage)** | ✅ Healthy | 9000/9001 | http://localhost:9001 (Console) |
| **Spark Master**           | ✅ Healthy | 7077/8088 | http://localhost:8088           |
| **Spark Worker**           | ✅ Running | 8089      | http://localhost:8089           |
| **PostgreSQL**             | ✅ Running | 5432      | Internal                        |

To stop and remove the services:

```powershell
./stop-services.sh
```

To scale Spark workers (example: run 3 workers):

```powershell
docker-compose up -d --scale spark-worker=3
```

Note: Airflow, MinIO and Spark are attached to the same Docker network so DAGs can reach services by their container names (for example `minio:9000` and `spark-master:7077`).

If you plan to deploy to a managed Airflow environment, adapt the Docker images and deployment steps accordingly — this repository focuses on a local Docker Compose development setup.

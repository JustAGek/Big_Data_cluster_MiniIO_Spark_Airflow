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

Start the full local stack (MinIO, Spark, Postgres, Airflow) with Docker Compose:

```powershell
./start-services.sh
```

This will build and start the following services:

- MinIO (object storage) — ports: 9000 (API), 9001 (Console)
- Spark Master & Worker(s) — master ports: 7077 (RPC), 8088 (UI) and worker UI on 8089
- Postgres — used by Airflow
- Airflow Webserver & Scheduler — Airflow UI at http://localhost:8080 (default admin/admin created)

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

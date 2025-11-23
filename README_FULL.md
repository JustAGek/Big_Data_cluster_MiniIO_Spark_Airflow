# afsparkmini — Local Airflow + Spark + MinIO development stack

This repository provides a self-contained local development stack for building and testing a Spark-based data pipeline backed by S3-compatible object storage (MinIO) and orchestrated by Apache Airflow. It was created to run the scalable financial fraud detection proof-of-concept used in the project proposal.

This README documents the full developer workflow: what services run, how to start/stop them, where to put the PaySim CSV files, how to upload them into MinIO, how to run the smoke tests, and common troubleshooting tips.

Contents
- `dags/` — Airflow DAGs (including smoke and Spark submission DAGs).
- `spark/` — Docker context for building Spark images used by the compose stack.
- `spark-jobs/` — PySpark jobs (e.g., `process_data.py`).
- `include/` — helper scripts and utilities (e.g., `upload_test_data.py`).
- `data/paysim/raw/` — (local) place for PaySim CSV files (created for you).
- `docker-compose.yml` — compose file that runs MinIO, Spark, Postgres, and Airflow locally.
- `start-services.sh` / `stop-services.sh` — convenience scripts to start/stop the stack.

Quick architecture summary
- Airflow (Webserver + Scheduler) manages DAGs and triggers spark-submits.
- MinIO acts as the S3-compatible object store for raw/processed data (Datalake).
- Spark master & workers run PySpark jobs that read/write data from/to MinIO via the S3A connector.
- Postgres is the Airflow metadata DB.

Service ports (container vs host mapping)
- Container internal ports (container-to-container):
  - MinIO API: `9000` (container), MinIO Console: `9001` (container)
  - Spark Master RPC: `7077`, Spark Master UI: `8088`, Spark Worker UI: `8089`
  - Airflow Webserver: `8080`, Postgres: `5432`
- Host ports (this repo maps MinIO to unusual host ports to avoid conflicts):
  - Airflow UI: http://localhost:8080
  - MinIO Console (host-mapped): http://localhost:19000  (API endpoint: http://localhost:19000)
  - Spark Master UI: http://localhost:8088
  - Spark Master RPC: spark://localhost:7077

Prerequisites
- Docker (Desktop) installed and running.
- docker-compose (v1 or v2; your Docker Desktop typically includes it).
- Python 3.8+ available on the host if you want to run the helper upload scripts or tests locally.

Where to put the PaySim CSV files (you asked)
- Local directory (created for you):

  `C:\Users\JustAGeek\Desktop\New folder\SIC_Graduation\afsparkmini\data\paysim\raw`

- Recommended naming conventions (the project pipeline expects daily splits):
  - `paysim_day_01.csv`, `paysim_day_02.csv`, …, `paysim_day_30.csv`
  - or a single file `paysim_full.csv` if you prefer one-file ingestion first.

How to start the entire stack (PowerShell)
1. From the repository root (Windows PowerShell):

```powershell
# Start services in detached mode
docker-compose up -d --build

# Wait a short while for services to initialize, then check status
docker-compose ps
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

2. Access UIs (host):
- Airflow UI: http://localhost:8080
- MinIO Console: http://localhost:19000 (or check `docker ps` for the mapped host port)
- Spark Master UI: http://localhost:8088

Stopping the stack (PowerShell)

```powershell
docker-compose down --volumes --remove-orphans
```

Uploading PaySim CSVs into MinIO
- The DAGs read from MinIO (`s3a://input-bucket`) so files must be uploaded to the `input-bucket` in MinIO for the pipeline to process them.
- There is a helper script at `include/upload_test_data.py`. It contains `get_minio_client()` and upload helper functions. By default the helper expects the MinIO endpoint available at `http://minio:9000` (container network). When running from your host you should point it to the host-mapped port `http://localhost:19000`.

Example — upload one file from PowerShell (adjust path and filename):

```powershell
$env:MINIO_ENDPOINT = "http://localhost:19000"
$env:MINIO_ACCESS_KEY = "minioadmin"
$env:MINIO_SECRET_KEY = "minioadmin"

python - <<'PY'
from include.upload_test_data import get_minio_client
client = get_minio_client()
bucket = 'input-bucket'
try:
    client.create_bucket(Bucket=bucket)
except Exception:
    pass
path = r"data\\paysim\\raw\\paysim_day_01.csv"  # change to your file
with open(path, 'rb') as f:
    client.put_object(Bucket=bucket, Key='paysim_day_01.csv', Body=f)
print('Uploaded paysim_day_01.csv to input-bucket')
PY
```

Tip: I can add a small CLI script `tools/upload_paysim.py` to bulk-upload everything under `data/paysim/raw` with one command — tell me if you want that.

Running the smoke test (pytest)
- Tests live in `tests/`. To run the smoke integration test that triggers the sample DAG:

```powershell
python -m pytest -q tests/test_smoke_workflow.py::test_smoke_pipeline_completes
```

The smoke test exercises the pipeline end-to-end: it uploads a sample file to MinIO, triggers the DAG via Airflow's REST API, waits for completion and asserts expected artifacts.

Common troubleshooting
- Airflow DAG import errors:
  - If the scheduler shows DAG parse/import exceptions, check your DAG files in `dags/` for provider-specific imports. Some DAGs include defensive try/except imports — this pattern is recommended when running in many environments.
  - When you change DAGs, delete Python bytecode caches inside the container to force recompilation: remove `/opt/airflow/dags/__pycache__` in the Airflow container or restart the scheduler.

- Airflow REST API 401 Unauthorized:
  - The compose environment enables basic auth via `AIRFLOW__API__AUTH_BACKENDS=airflow.api.auth.backend.basic_auth`. Use your configured username/password when calling the REST API.

- Spark S3A NumberFormatException ("For input string: \"60s\""):
  - This repository encountered a Hadoop/S3A configuration problem where unit-suffixed values (e.g. "60s") were present in defaults and caused a Java NumberFormatException. Workarounds implemented here:
    1. The DAGs pass numeric overrides to `spark-submit` using `--conf spark.hadoop.fs.s3a.socket.timeout=60000` (milliseconds) and related keys.
    2. The Spark job (`spark-jobs/process_data.py`) also sets the numeric configs on the SparkSession to ensure values are numeric.
  - If you see the `NumberFormatException` on startup, add numeric `spark.hadoop.fs.s3a.*` configs (milliseconds or integer counts) to both the DAG `spark-submit` and the SparkSession builder.

- MinIO connectivity from host vs container:
  - Inside containers use `http://minio:9000`.
  - From host use `http://localhost:19000` (or the host port `docker ps` shows).

Developer notes & extension points
- To make the S3A numeric-workaround permanent, you can bake `core-site.xml` with the correct numeric values into the Spark image (`spark/Dockerfile`). This avoids passing overrides repeatedly at runtime.
- To add new DAGs, put them in `dags/` and follow the defensive import pattern for optional providers:

```python
try:
    from airflow.providers.amazon.aws.operators.sagemaker import SageMakerCreateTrainingJobOperator
except Exception:
    SageMakerCreateTrainingJobOperator = None
```

- The Spark jobs are in `spark-jobs/`. Use `spark-submit` arguments in the DAGs — the DAGs already include recommended `--conf` overrides for S3A timeouts and retries.

Useful commands (PowerShell)

```powershell
# Show compose services and their status
docker-compose ps

# Show running containers with ports
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# View Airflow logs (container)
docker-compose logs -f airflow-scheduler

# Execute spark-submit from inside the spark-master container (example)
docker exec -it spark-master /bin/bash
# then run spark-submit inside container where spark, hadoop classpath and credentials are available
```

Contact / support
- If you find issues, please open an issue in this repo describing the error and include relevant container logs (`docker-compose logs <service>`).

License
- This repository is provided as-is for learning and prototyping. Adapt and reuse as needed.

Acknowledgements
- The stack is assembled to simulate a cloud-native lakehouse locally using MinIO and Spark and is intended for the Samsung Innovation Campus project described in the proposal.

---

If you want, I can also:
- add a `tools/upload_paysim.py` script to bulk-upload files from `data/paysim/raw` into MinIO, and/or
- add a small CI job or script to run the smoke tests with a single command, and/or
- bake the numeric S3A overrides into the Spark image by adding a `core-site.xml` into `spark/` and rebuilding the Spark image.

Tell me which extras you'd like and I'll implement them next.

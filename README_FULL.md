# Big Data Cluster: Financial Fraud Detection Pipeline

## Complete Developer Guide

**Project**: Samsung Innovation Campus (SIC) Graduation Project  
**Focus**: Financial fraud detection using Apache Spark, MinIO, and Airflow  
**Last Updated**: November 2025

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start)
5. [System Architecture & Components](#system-architecture--components)
6. [Configuration](#configuration)
7. [Running Pipelines](#running-pipelines)
8. [Data Flow](#data-flow)
9. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
10. [Development Guide](#development-guide)
11. [Performance Tuning](#performance-tuning)
12. [Production Deployment](#production-deployment)

---

## Project Overview

This repository implements a **financial fraud detection system** using:

- **Apache Airflow**: Workflow orchestration and scheduling
- **Apache Spark**: Distributed data processing and analytics
- **MinIO**: S3-compatible object storage for datalake
- **PostgreSQL**: Airflow metadata database
- **Snowflake**: Cloud data warehouse for final processed data (optional)

### Key Features

✅ **Local Development Stack**: Fully containerized for easy local development  
✅ **End-to-End Pipeline**: Data ingestion → transformation → analytics  
✅ **Fraud Detection**: ML-ready feature engineering on PaySim transaction data  
✅ **Scalable**: Auto-scale Spark workers as needed  
✅ **Production-Ready**: Includes error handling, retries, and comprehensive logging

---

## Architecture

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL DATA SOURCES                       │
│              (PaySim CSVs, Other Transaction Feeds)             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 AIRFLOW ORCHESTRATION LAYER                     │
│                    (Airflow Scheduler)                          │
│           DAG: fintech_fraud_pipeline_v4                        │
└─────┬──────────────────────────────────────────────────────┬────┘
      │                                                      │
      ▼ (Task 1)                                   (Task 2) ▼
┌─────────────────────┐                      ┌──────────────────────┐
│  INGEST_TO_MINIO    │                      │ PROCESS_WITH_SPARK   │
│ (Python Operator)   │                      │(SparkSubmitOperator) │
│                     │                      │                      │
│ Upload CSV to      ├─────────────────────>│ Read S3A → Transform │
│ MinIO raw-data     │                      │ → Write to Snowflake │
│ bucket             │                      │                      │
└─────────────────────┘                      └──────────────────────┘
      │                                                 │
      ▼                                                 ▼
┌────────────────────┐                      ┌──────────────────────┐
│     MinIO          │                      │   Spark Cluster      │
│   (Storage)        │                      │ Master + Workers     │
│                    │                      │                      │
│ input: raw-data    │◄─────────────────────┤ (Distributed Compute)│
│ output: (for later)│                      │                      │
└────────────────────┘                      └──────────────────────┘
      │                                                 │
      │                                                 ▼
      │                                      ┌──────────────────────┐
      │                                      │     Snowflake DW     │
      │                                      │                      │
      │                                      │ Table:               │
      │                                      │ FACT_TRANSACTIONS    │
      └──────────────────────────────────────┤                      │
         (Optional: Archive to processed)    │ (Optional Connection)│
                                             └──────────────────────┘
```

### Data Flow

```
RAW DATA
  ↓
/include/data/paysim/raw/paysim_day*.csv
  ↓
Python Operator (upload_to_minio)
  ↓
MinIO: s3a://raw-data/paysim_day*.csv
  ↓
Spark Job (process_fraud_data.py)
  ├─ Read CSV from MinIO
  ├─ Transform:
  │  ├─ Generate unique transaction ID (MD5 hash)
  │  ├─ Add ingestion timestamp
  │  ├─ Cast data types (amounts to double, step to int, etc.)
  │  └─ Rename columns to uppercase
  ├─ Feature engineering:
  │  ├─ Balance changes
  │  ├─ Fraud indicators
  │  └─ Transaction metadata
  └─ Write to Snowflake
      ↓
FACT_TRANSACTIONS table (Snowflake)
```

---

## Prerequisites

### System Requirements

- **Docker Desktop** or Docker Engine (v20.10+)
- **Docker Compose** (v1.29+ or v2.0+)
- **Git** (for cloning the repository)
- **Python 3.8+** (optional, for local testing)
- **4GB+ RAM** (recommended for Docker allocation)
- **20GB+ disk space** (for images and volumes)

### Software to Install

```powershell
# Verify Docker and Compose are installed
docker --version      # Docker 20.10+
docker-compose --version  # 1.29+ or 2.0+

# For local testing (optional)
python --version      # 3.8+
pip install pytest requests
```

---

## Quick Start

### 1. Clone and Navigate to Project

```powershell
cd "Big_Data_cluster_MiniIO_Spark_Airflow"
```

### 2. Start the Stack

```powershell
# Start all services (MinIO, Spark, Airflow, Postgres)
./start-services.sh

# Wait for initialization (30-60 seconds)
sleep 30

# Verify all services are running
docker-compose ps
```

### 3. Access the UIs

Open your browser and navigate to:

| Service          | URL                   | Login                       |
| ---------------- | --------------------- | --------------------------- |
| **Airflow**      | http://localhost:8080 | `admin` / `admin`           |
| **MinIO**        | http://localhost:9001 | `minioadmin` / `minioadmin` |
| **Spark Master** | http://localhost:8088 | -                           |

### 4. Run the Pipeline

1. **Open Airflow UI** → http://localhost:8080
2. **Find DAG**: `fintech_fraud_pipeline_v4`
3. **Enable DAG**: Toggle the switch to ON
4. **Trigger**: Click the ▶️ button to run manually
5. **Monitor**: Click on the DAG run to see task progress

### 5. Stop the Stack

```powershell
./stop-services.sh
```

---

## System Architecture & Components

### Services Breakdown

#### 1. Airflow (Orchestration)

**Role**: Schedules and monitors data pipelines

**Containers**:

- `airflow-webserver`: Web UI (port 8080)
- `airflow-scheduler`: Task scheduler and executor
- `airflow-init`: One-time initialization

**Configuration**:

- Executor: LocalExecutor (single-machine execution)
- Database: PostgreSQL (metadata storage)
- Connections: Pre-configured for Spark and MinIO

**Key Files**:

- `airflow/Dockerfile`: Custom Airflow image
- `airflow/requirements.txt`: Python dependencies
- `airflow/load_connections.sh`: Connection setup script
- `dags/fraud_pipeline_dag.py`: Main pipeline definition

#### 2. Spark (Distributed Processing)

**Role**: Large-scale data transformation and analytics

**Containers**:

- `spark-master`: Master node (port 7077 RPC, 8088 UI)
- `spark-worker`: Worker nodes (port 8089+ UI)

**Configuration**:

- 2 cores per worker
- 2GB memory per worker
- Scalable via `--scale spark-worker=N`

**Key Files**:

- `spark/Dockerfile`: Spark runtime image
- `spark-jobs/process_fraud_data.py`: ETL job

#### 3. MinIO (Object Storage)

**Role**: S3-compatible data datalake

**Container**: `minio` (port 9000 API, 9001 Console)

**Buckets**:

- `raw-data`: Input CSV files
- `input-bucket`: Legacy bucket (may be deprecated)
- `output-bucket`: Legacy output
- `processed-data`: Processed results

**Credentials**: `minioadmin` / `minioadmin`

#### 4. PostgreSQL (Metadata Database)

**Role**: Airflow state and DAG metadata

**Container**: `postgres` (port 5432, internal only)

**Database**: `airflow` (created automatically)

---

## Configuration

### Environment Variables (.env file)

Create a `.env` file in the project root with the following variables:

```env
# MinIO Configuration
MINIO_PORT=9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_HOST=minio

# Spark Configuration
SPARK_MASTER_HOST=spark-master
SPARK_MASTER_PORT=7077
SPARK_MASTER_WEBUI_PORT=8088
SPARK_WORKER_CORES=2
SPARK_WORKER_MEMORY=2g
SPARK_WORKER_PORT=7078
SPARK_WORKER_WEBUI_PORT=8089

# PostgreSQL Configuration
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow123
POSTGRES_DB=airflow

# Airflow Configuration
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__FERNET_KEY=your_fernet_key_here
AIRFLOW__WEBSERVER__WORKERS=2
AIRFLOW_FERNET_KEY=your_fernet_key_here

# Snowflake Configuration (Optional)
SNOWFLAKE_USER=your_sf_user
SNOWFLAKE_PASSWORD=your_sf_password
SNOWFLAKE_ACCOUNT=your_account_id
SNOWFLAKE_DB=FRAUD_DETECTION
SNOWFLAKE_SCHEMA=FRAUD_DETECTION
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_ROLE=ACCOUNTADMIN
```

### Docker Compose Configuration

**File**: `docker-compose.yml`

Key services and their configurations:

```yaml
minio:
  - S3-compatible storage
  - Volumes: minio-data (persistent)
  - Buckets auto-created by minio-init service

spark-master:
  - Spark cluster leader
  - Ports: 7077 (RPC), 8088 (Web UI)

spark-worker:
  - Spark compute nodes (scalable)
  - Ports: 8089 (Web UI), 7078 (RPC)

postgres:
  - Airflow metadata DB
  - Volumes: pgdata (persistent)

airflow-init:
  - One-time setup: DB upgrade, create admin user, load connections
  - Must complete before webserver/scheduler starts

airflow-webserver:
  - Web UI for DAG management
  - Port: 8080

airflow-scheduler:
  - Task scheduling and monitoring
  - Runs DAGs on schedule or manual trigger
```

---

## Running Pipelines

### DAG: fintech_fraud_pipeline_v4

**Purpose**: End-to-end fraud detection pipeline

**Schedule**: `@daily` (daily at 00:00 UTC) or manual trigger

**Tasks**:

#### Task 1: ingest_to_minio

```python
PythonOperator
├─ Reads PaySim CSV from: /opt/airflow/include/data/paysim/raw/
├─ Connects to MinIO via boto3 (http://minio:9000)
├─ Uploads file to bucket: raw-data
└─ Expected duration: < 1 minute
```

**Code Location**: `dags/fraud_pipeline_dag.py` (function: `upload_to_minio`)

**Inputs**:

- CSV file path: `/opt/airflow/include/data/paysim/raw/paysim_day{N}.csv`
- MinIO endpoint: `http://minio:9000`
- Credentials: `minioadmin`/`minioadmin`

**Outputs**:

- File in MinIO: `s3a://raw-data/paysim_day{N}.csv`

#### Task 2: process_with_spark

```python
SparkSubmitOperator
├─ Submits Spark job to Spark Master
├─ Job: process_fraud_data.py
├─ Reads from MinIO (S3A)
├─ Transforms data
└─ Writes to Snowflake (if configured)
```

**Code Location**: `spark-jobs/process_fraud_data.py`

**Transformations**:

- Generate unique transaction ID via MD5 hash
- Add ingestion timestamp
- Cast data types (numeric fields to double/int)
- Rename columns to uppercase
- Derive features (balance changes, fraud flags)

**Output**:

- Snowflake table: `FACT_TRANSACTIONS`
- Columns: TRANS_ID, STEP, TYPE, AMOUNT, NAME_ORIG, etc.

### Manually Trigger a DAG Run

**Via Airflow UI**:

1. Go to http://localhost:8080
2. Click on `fintech_fraud_pipeline_v4`
3. Click the ▶️ "Trigger DAG" button
4. (Optional) Set run ID or parameters

**Via Airflow REST API**:

```powershell
$dag_id = "fintech_fraud_pipeline_v4"
$run_id = "manual_run_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

curl -X POST `
  -H "Content-Type: application/json" `
  -d "{`"dag_run_id`": `"$run_id`"}" `
  -u admin:admin `
  "http://localhost:8080/api/v1/dags/$dag_id/dagRuns"
```

### Monitor DAG Execution

1. **Airflow UI**: Watch task status change from `queued` → `running` → `success`
2. **Task Logs**: Click a task to view detailed logs
3. **Spark Master UI**: http://localhost:8088 to see Spark jobs
4. **Container Logs**:

```powershell
# Airflow Scheduler logs
docker-compose logs -f airflow-scheduler

# Spark Master logs
docker-compose logs -f spark-master

# Spark Worker logs
docker-compose logs -f spark-worker

# MinIO logs
docker-compose logs -f minio
```

---

## Data Flow

### Step-by-Step Data Journey

#### 1. Data Preparation (Local or External)

**Source**: PaySim dataset (CSV format)

**Location**: Place files in `include/data/paysim/raw/`

**File Format**:

```csv
step,type,amount,nameOrig,oldbalanceOrg,newbalanceOrig,nameDest,oldbalanceDest,newbalanceDest,isFraud,isFlaggedFraud
1,CASH_OUT,100.0,C1,500.0,400.0,C2,1000.0,1100.0,0,0
2,TRANSFER,50.0,C1,400.0,350.0,C3,500.0,550.0,1,0
```

#### 2. Ingestion Phase (Airflow Task 1)

**Actor**: `ingest_to_minio` (PythonOperator)

**Steps**:

1. Airflow reads the file from `/opt/airflow/include/data/paysim/raw/paysim_day1.csv`
2. Creates boto3 S3 client pointing to MinIO (`http://minio:9000`)
3. Uploads file to MinIO bucket `raw-data` with same filename
4. Returns success/failure status

**Error Handling**:

- File not found → Raises `FileNotFoundError`
- MinIO connection error → Raises exception with details
- Airflow retries logic configured: 0 retries (can be modified)

#### 3. Processing Phase (Spark Job)

**Actor**: `process_with_spark` (SparkSubmitOperator)

**Steps**:

1. Spark reads file from `s3a://raw-data/paysim_day1.csv` via S3A connector
2. Parses CSV with header and schema inference
3. Applies transformations:
   - Generate MD5 hash for TRANS_ID from step + nameOrig + amount
   - Add INGESTION_TIMESTAMP (current_timestamp)
   - Cast numeric columns to proper types
   - Rename columns to uppercase
4. Writes to Snowflake FACT_TRANSACTIONS table (append mode)

**Spark Configuration**:

```python
spark.hadoop.fs.s3a.endpoint = http://minio:9000
spark.hadoop.fs.s3a.access.key = minioadmin
spark.hadoop.fs.s3a.secret.key = minioadmin
spark.hadoop.fs.s3a.path.style.access = true
spark.hadoop.fs.s3a.impl = org.apache.hadoop.fs.s3a.S3AFileSystem
spark.hadoop.fs.s3a.connection.ssl.enabled = false
```

#### 4. Storage Phase

**MinIO** (S3A):

- File remains in `raw-data/paysim_day1.csv`

**Snowflake** (if configured):

- Data inserted into `FRAUD_DETECTION.FRAUD_DETECTION.FACT_TRANSACTIONS`

---

## Monitoring & Troubleshooting

### Monitoring Tools

#### 1. Airflow Web UI

- **URL**: http://localhost:8080
- **Shows**: DAGs, task status, logs, metrics
- **Key Views**:
  - Graph View: Visual task dependencies
  - Tree View: Historical runs
  - Task Logs: Detailed execution output

#### 2. Spark Master UI

- **URL**: http://localhost:8088
- **Shows**: Running/completed applications, executors, stage details
- **Key Sections**:
  - Running Applications
  - Completed Applications
  - Executors (task capacity)
  - Stages (performance metrics)

#### 3. MinIO Console

- **URL**: http://localhost:9001
- **Shows**: Buckets, objects, access logs
- **Can**: Upload/download files, manage buckets, set policies

#### 4. Docker Logs

```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f airflow-scheduler
docker-compose logs -f spark-master
docker-compose logs -f minio

# Last N lines
docker-compose logs --tail=50 airflow-webserver
```

### Common Issues & Solutions

#### Issue 1: Airflow DAG Not Appearing

**Symptoms**: DAG not visible in Airflow UI after `./start-services.sh`

**Solutions**:

1. Check if `airflow-init` completed successfully:

   ```powershell
   docker-compose logs airflow-init
   ```

2. Restart the scheduler:

   ```powershell
   docker-compose restart airflow-scheduler
   ```

3. Check DAG file syntax:
   ```powershell
   docker exec airflow-webserver python -m py_compile /opt/airflow/dags/fraud_pipeline_dag.py
   ```

#### Issue 2: Spark Job Fails with S3A Connection Error

**Symptoms**: `java.lang.NumberFormatException` or connection timeout

**Solutions**:

1. Verify MinIO is running:

   ```powershell
   docker-compose ps minio
   curl http://localhost:9000/minio/health/live
   ```

2. Check Spark configuration in DAG:

   - Socket timeout should be numeric (milliseconds)
   - Path style access enabled
   - SSL disabled (for local MinIO)

3. View Spark logs:
   ```powershell
   docker logs spark-master
   docker logs spark-worker
   ```

#### Issue 3: Task Fails - File Not Found at `/opt/airflow/include/data/paysim/raw/`

**Symptoms**: `FileNotFoundError` during ingest task

**Solutions**:

1. Place PaySim CSV in the correct location (host):

   ```powershell
   ls include/data/paysim/raw/  # Should show paysim_day*.csv
   ```

2. Verify the file was mounted into Airflow container:

   ```powershell
   docker exec airflow-webserver ls /opt/airflow/include/data/paysim/raw/
   ```

3. Check docker-compose.yml volume mount for Airflow services

#### Issue 4: Snowflake Connection Failed

**Symptoms**: Spark job completes but Snowflake write fails

**Solutions**:

1. Verify Snowflake credentials in `.env`:

   ```powershell
   echo $env:SNOWFLAKE_ACCOUNT, $env:SNOWFLAKE_USER
   ```

2. Check Snowflake is accessible:

   - URL format: `https://{account}.snowflakecomputing.com`
   - Test connection manually

3. Verify warehouse is running in Snowflake console

4. View Spark error logs:
   ```powershell
   docker logs spark-master | grep -i snowflake
   ```

#### Issue 5: Out of Memory or Cluster Performance Issues

**Symptoms**: Tasks timeout, containers crash, slow processing

**Solutions**:

1. Check Docker memory allocation:

   ```powershell
   docker stats
   ```

2. Increase worker resources in `.env`:

   ```env
   SPARK_WORKER_CORES=4      # Increase from 2
   SPARK_WORKER_MEMORY=4g    # Increase from 2g
   ```

3. Rebuild and restart:

   ```powershell
   docker-compose down -v
   docker-compose up -d --build
   ```

4. Or add more workers:
   ```powershell
   docker-compose up -d --scale spark-worker=3
   ```

---

## Development Guide

### Adding a New DAG

**Example**: Create a new pipeline for additional data sources

```python
# dags/my_new_pipeline.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 1, 1),
}

with DAG(
    'my_custom_pipeline',
    default_args=default_args,
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    catchup=False,
) as dag:

    # Task 1: Extract
    extract_task = PythonOperator(
        task_id='extract_data',
        python_callable=my_extract_function,
    )

    # Task 2: Transform (Spark)
    transform_task = SparkSubmitOperator(
        task_id='transform_data',
        conn_id='spark_default',
        application='/opt/spark-jobs/my_transform.py',
        verbose=True
    )

    extract_task >> transform_task
```

**Steps**:

1. Create `dags/my_new_pipeline.py`
2. Define DAG with unique `dag_id`
3. Add tasks (Python operators, Spark operators, etc.)
4. Define task dependencies with `>>`
5. Airflow auto-discovers the DAG (no restart needed)

### Creating a New Spark Job

**Example**: Custom data transformation

```python
# spark-jobs/my_transform.py

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp

def main():
    spark = SparkSession.builder \
        .appName("MyTransform") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
        .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
        .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .getOrCreate()

    # Read from MinIO
    df = spark.read.csv("s3a://raw-data/myfile.csv", header=True)

    # Transform
    df_transformed = df \
        .withColumn("processing_date", current_timestamp()) \
        .filter(col("amount") > 0)

    # Write to MinIO or Snowflake
    df_transformed.write \
        .csv("s3a://processed-data/output", mode="overwrite", header=True)

    spark.stop()

if __name__ == "__main__":
    main()
```

### Testing Locally

**Run Integration Tests**:

```powershell
# Ensure stack is running
./start-services.sh

# Run smoke tests
python -m pytest tests/test_smoke_workflow.py -v

# Run specific test
python -m pytest tests/test_smoke_workflow.py::test_smoke_pipeline_completes -v
```

**What the Smoke Test Does**:

1. Triggers the `smoke_test_pipeline` DAG
2. Waits for completion (default 300 seconds)
3. Verifies all tasks succeeded
4. Reports any failures

---

## Performance Tuning

### Spark Optimization

#### 1. Increase Parallelism

```python
spark.conf.set("spark.sql.shuffle.partitions", 200)
spark.conf.set("spark.default.parallelism", 200)
```

#### 2. Tune Executor Resources

In `.env`:

```env
SPARK_EXECUTOR_CORES=4
SPARK_EXECUTOR_MEMORY=4g
SPARK_DRIVER_MEMORY=2g
```

#### 3. Optimize S3A Access

```python
spark.config("spark.hadoop.fs.s3a.block.size", "128M")
spark.config("spark.hadoop.fs.s3a.threads.max", "100")
spark.config("spark.hadoop.fs.s3a.connection.establish.timeout", "50000")
```

### MinIO Optimization

#### 1. Increase Concurrent Requests

```yaml
environment:
  MINIO_API_CORS_ALLOW_ORIGIN: "*"
  MINIO_STORAGE_CLASS_STANDARD: "EC:3"
```

#### 2. Monitor Storage Usage

```powershell
docker exec minio mc du minio/raw-data
```

### Airflow Optimization

#### 1. Increase Webserver Workers

In `.env`:

```env
AIRFLOW__WEBSERVER__WORKERS=4
```

#### 2. Configure DAG Parsing

```env
AIRFLOW__CORE__PARALLELISM=32
AIRFLOW__CORE__DAG_CONCURRENCY=16
```

---

## Production Deployment

### Pre-Production Checklist

- [ ] Snowflake credentials configured and tested
- [ ] Data validation rules implemented
- [ ] Error alerting configured (email notifications)
- [ ] Backup strategy for MinIO data
- [ ] Resource limits set appropriately
- [ ] Monitoring and logging enabled
- [ ] Security review complete (credentials, network)

### Deployment Steps

1. **Deploy on Cloud VM**:

   - Install Docker and Docker Compose
   - Clone repository
   - Configure `.env` with production credentials

2. **Use Managed Services** (Recommended):

   - Replace local Airflow with cloud Airflow (AWS MWAA, GCP Cloud Composer)
   - Replace MinIO with cloud storage (AWS S3, GCS)
   - Use cloud data warehouse (Snowflake, BigQuery, Redshift)

3. **Security Hardening**:

   - Use Docker secrets for credentials
   - Enable TLS for all services
   - Configure network policies
   - Implement access controls

4. **Monitoring**:
   - Set up Prometheus + Grafana
   - Configure alerting thresholds
   - Log aggregation (ELK stack)
   - APM tools for Spark

---

## Useful Commands

### Docker Compose Commands

```powershell
# Start stack
docker-compose up -d --build

# View status
docker-compose ps

# View logs (all)
docker-compose logs -f

# View logs (specific service, last 50 lines)
docker-compose logs --tail=50 -f airflow-scheduler

# Stop stack
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Scale workers
docker-compose up -d --scale spark-worker=3

# Restart specific service
docker-compose restart spark-master
```

### Airflow Commands (inside container)

```powershell
# Access Airflow container
docker exec -it airflow-webserver bash

# Inside container:
# List DAGs
airflow dags list

# Trigger DAG
airflow dags trigger fintech_fraud_pipeline_v4

# View task logs
airflow tasks logs fintech_fraud_pipeline_v4 ingest_to_minio <run_id>

# Test DAG syntax
airflow dags test fintech_fraud_pipeline_v4

# View connections
airflow connections list
```

### Spark Commands (inside container)

```powershell
# Access Spark Master
docker exec -it spark-master bash

# Inside container:
# Submit job
spark-submit --master spark://spark-master:7077 /opt/spark-jobs/process_fraud_data.py

# View Spark logs
tail -f /opt/spark/logs/spark*.log
```

### MinIO Commands (inside container)

```powershell
# Access MinIO init container
docker exec -it minio-init bash

# Inside container (using mc CLI):
# List buckets
mc ls minio/

# List bucket contents
mc ls minio/raw-data

# Upload file
mc cp myfile.csv minio/raw-data/

# Remove file
mc rm minio/raw-data/myfile.csv
```

---

## Additional Resources

- [Apache Airflow Docs](https://airflow.apache.org/)
- [Apache Spark Docs](https://spark.apache.org/docs/latest/)
- [MinIO Documentation](https://docs.min.io/)
- [PaySim Dataset Paper](https://www.kaggle.com/datasets/ealaxi/paysim1)
- [S3A Configuration Guide](https://hadoop.apache.org/docs/current/hadoop-aws/tools/hadoop-aws/index.html)

---

## Support & Contribution

For issues, feature requests, or contributions:

1. Check existing logs and troubleshooting guide
2. Review docker-compose.yml and DAG files
3. Consult service documentation (Airflow, Spark, MinIO)
4. Open an issue with:
   - Error logs (docker-compose logs)
   - Steps to reproduce
   - Environment details (.env, OS, Docker version)

---

**Last Updated**: November 24, 2025  
**Project**: SIC Graduation - Big Data Fraud Detection  
**Maintainer**: Development Team

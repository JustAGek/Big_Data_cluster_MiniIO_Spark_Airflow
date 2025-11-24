# Spark + MinIO + Airflow Local Setup Guide

## Overview

This guide covers the setup and operation of a local Big Data cluster for financial fraud detection using:

- **Apache Spark** (distributed processing)
- **MinIO** (S3-compatible object storage)
- **Apache Airflow** (workflow orchestration)
- **PostgreSQL** (metadata storage)

All services run as Docker containers on a single shared network for seamless inter-service communication.

---

## System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    DOCKER NETWORK: spark-minio-network        │
│                                                                │
│  ┌──────────────┐         ┌──────────────┐                   │
│  │   MinIO      │         │   Airflow    │                   │
│  │ (S3-compat)  │◄───────►│ (Orchestrate)│                   │
│  │ Port: 9000   │         │ Port: 8080   │                   │
│  └──────────────┘         └──────────────┘                   │
│        ▲                          ▲                            │
│        │                          │                            │
│        └──────────────┬───────────┘                            │
│                       ▼                                         │
│               ┌──────────────────┐                             │
│               │   Spark Cluster  │                             │
│               │ Master: 7077     │                             │
│               │ Master UI: 8088  │                             │
│               │ Workers: 7078+   │                             │
│               └──────────────────┘                             │
│                       ▲                                         │
│                       │                                         │
│               ┌────────────────┐                               │
│               │   PostgreSQL   │                               │
│               │  (Airflow DB)  │                               │
│               └────────────────┘                               │
└────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Hardware Requirements

- **CPU**: Dual-core minimum (4+ cores recommended)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 30GB available for Docker images and volumes

### Software Requirements

```powershell
# Check versions
docker --version        # 20.10.0 or newer
docker-compose --version  # 1.29.0 or newer (or v2.0+)
git --version          # Any recent version
```

### Installation

If not already installed:

1. **Install Docker Desktop** (includes Docker and Docker Compose):

   - Download: https://www.docker.com/products/docker-desktop
   - Follow installation guide for Windows/Mac/Linux

2. **Verify Installation**:
   ```powershell
   docker run hello-world
   docker-compose version
   ```

---

## Quick Start (5 Minutes)

### Step 1: Clone the Repository

```powershell
git clone <repository-url>
cd Big_Data_cluster_MiniIO_Spark_Airflow
```

### Step 2: Start the Stack

```powershell
# Using the convenience script (recommended)
./start-services.sh

# Or using Docker Compose directly
docker-compose up -d --build
```

### Step 3: Wait for Initialization

The stack takes 30-60 seconds to fully initialize:

```powershell
# Monitor startup
docker-compose ps

# Wait until all services show "Up" status
# Once ready, all containers should be healthy
```

### Step 4: Access Services

| Service         | URL                   | Credentials             |
| --------------- | --------------------- | ----------------------- |
| Airflow Web UI  | http://localhost:8080 | admin / admin           |
| MinIO Console   | http://localhost:9001 | minioadmin / minioadmin |
| Spark Master UI | http://localhost:8088 | -                       |
| Spark Worker UI | http://localhost:8089 | -                       |

### Step 5: Trigger Your First Pipeline

1. Open **http://localhost:8080** (Airflow)
2. Find DAG: **`fintech_fraud_pipeline_v4`**
3. Toggle switch to **ON**
4. Click **▶️ Play** to trigger
5. Monitor task progress in the UI

### Step 6: Stop the Stack

```powershell
./stop-services.sh
# or
docker-compose down -v  # Removes volumes too
```

---

## Detailed Service Configuration

### 1. MinIO (Object Storage)

#### Purpose

Acts as a self-hosted S3-compatible data lake for storing CSV files and processed data.

#### Access Methods

**From inside Docker (container-to-container)**:

```python
endpoint = "http://minio:9000"
access_key = "minioadmin"
secret_key = "minioadmin"
```

**From your host machine**:

```powershell
# Console (browser)
http://localhost:9001

# API endpoint (if needed)
http://localhost:9000
```

#### Buckets

The following buckets are created automatically:

| Bucket           | Purpose                 |
| ---------------- | ----------------------- |
| `raw-data`       | Input CSV files         |
| `input-bucket`   | Legacy input            |
| `output-bucket`  | Legacy output           |
| `processed-data` | Final processed results |

#### Upload Data to MinIO

**Option 1: MinIO Console (Web UI)**

1. Open http://localhost:9001
2. Login with `minioadmin` / `minioadmin`
3. Navigate to `raw-data` bucket
4. Click "Upload" and select your CSV

**Option 2: Python Script (from Airflow container)**

```powershell
docker exec -it airflow-webserver bash
python /opt/airflow/include/upload_test_data.py
```

**Option 3: AWS CLI**

```powershell
aws configure set aws_access_key_id minioadmin
aws configure set aws_secret_access_key minioadmin

aws s3 --endpoint-url http://localhost:9000 \
    cp paysim_day1.csv s3://raw-data/
```

---

### 2. Spark (Distributed Processing)

#### Components

**Spark Master**:

- Role: Cluster leader and resource manager
- RPC Port: 7077 (internal, spark-submit target)
- Web UI: http://localhost:8088
- Container: `spark-master`

**Spark Workers** (one or more):

- Role: Task execution nodes
- Web UI: http://localhost:8089 (first worker), 8090 (second), etc.
- Containers: `spark-worker`, `spark-worker_2`, etc.

#### Configuration

Edit `.env` to adjust Spark resources:

```env
SPARK_WORKER_CORES=2      # CPU cores per worker
SPARK_WORKER_MEMORY=2g    # RAM per worker
```

Example: To scale to 3 workers with more resources:

```powershell
# Edit .env
SPARK_WORKER_CORES=4
SPARK_WORKER_MEMORY=4g

# Scale workers
docker-compose up -d --scale spark-worker=3
```

#### Monitoring Jobs

1. Open **http://localhost:8088** (Spark Master UI)
2. Find your running application (e.g., "FraudDetectionETL")
3. Click to view:
   - Task execution progress
   - Memory and CPU usage
   - Stage breakdown
   - Executor details

#### Submitting Jobs Manually

```powershell
# Access Spark Master container
docker exec -it spark-master bash

# Inside container, submit job:
spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --executor-cores 2 \
  --executor-memory 2g \
  /opt/spark-jobs/process_fraud_data.py \
  paysim_day1.csv \
  http://minio:9000 \
  minioadmin minioadmin \
  sf_user sf_password sf_account sf_db sf_schema sf_warehouse sf_role
```

---

### 3. Airflow (Orchestration)

#### Services

**Airflow Webserver**:

- Web UI for DAG management
- Port: 8080
- Container: `airflow-webserver`
- URL: http://localhost:8080

**Airflow Scheduler**:

- Executes DAGs on schedule or manual trigger
- Container: `airflow-scheduler`
- Logs: `docker-compose logs -f airflow-scheduler`

**Airflow Init**:

- One-time setup: DB migration, admin user creation
- Container: `airflow-init`
- Completes before webserver and scheduler start

#### Default Credentials

- **Username**: `admin`
- **Password**: `admin`

Change these in production via Airflow UI (Admin → Users).

#### DAG Location

All DAGs should be placed in: `dags/`

Airflow auto-discovers DAGs (no restart needed after adding new files).

#### Pre-configured Connections

The `airflow-init` service automatically creates connections:

| Connection      | Type  | Host                      | Purpose              |
| --------------- | ----- | ------------------------- | -------------------- |
| `spark_default` | Spark | spark://spark-master:7077 | Submit Spark jobs    |
| `minio_default` | AWS   | minio:9000                | Access MinIO storage |

---

### 4. PostgreSQL (Metadata Database)

#### Purpose

Stores Airflow state, DAG metadata, user information, and task logs.

#### Access (Internal Only)

- **Host**: `postgres` (container name)
- **Port**: 5432
- **Database**: `airflow`
- **User**: `airflow`
- **Password**: `airflow123`

Not exposed to your host machine (internal Docker network only).

#### Persistent Storage

Database persists in Docker volume `pgdata`. Data survives container restarts.

---

## Common Tasks

### Task 1: Upload PaySim Data to MinIO

**Scenario**: You have CSV files to process

```powershell
# Option 1: Place files in include/data/paysim/raw/
# Then Airflow DAG will pick them up automatically

# Option 2: Upload via MinIO Console (Web UI)
# 1. Go to http://localhost:9001
# 2. Login: minioadmin / minioadmin
# 3. Navigate to 'raw-data' bucket
# 4. Click "Upload" → Select your CSV file

# Option 3: Upload via Python (inside Airflow container)
docker exec -it airflow-webserver bash
python -c "
from include.upload_test_data import get_minio_client
import os

client = get_minio_client()
file_path = '/opt/airflow/include/data/paysim/raw/paysim_day1.csv'

with open(file_path, 'rb') as f:
    client.put_object(
        'raw-data',
        'paysim_day1.csv',
        f,
        os.path.getsize(file_path)
    )
print('Upload complete!')
"
```

### Task 2: Monitor a Running Pipeline

```powershell
# 1. Open Airflow UI
# http://localhost:8080

# 2. Click on the DAG → Click on a running task

# 3. View logs:
docker-compose logs -f airflow-scheduler

# 4. Check Spark progress:
# http://localhost:8088 (applications tab)

# 5. Check MinIO file uploads:
# http://localhost:9001 (raw-data bucket)
```

### Task 3: Debug a Failed Task

```powershell
# Step 1: Check task logs in Airflow UI
# Navigate to DAG → Failed task → "Log" tab

# Step 2: View container logs for more context
docker-compose logs --tail=100 airflow-scheduler
docker-compose logs --tail=100 spark-master

# Step 3: Test Python code locally (inside container)
docker exec -it airflow-webserver bash
cd /opt/airflow/dags
python -c "
from fraud_pipeline_dag import upload_to_minio
# Test the function manually
"

# Step 4: Check file system and permissions
docker exec airflow-webserver ls -la /opt/airflow/include/data/paysim/raw/
```

### Task 4: Scale Spark Workers for More Compute

```powershell
# Current setup: 1 master + 1 worker

# Scale to 3 workers (increase parallelism):
docker-compose up -d --scale spark-worker=3

# Verify workers registered with master:
# http://localhost:8088 (check "Alive Workers" count)

# To increase worker resources, edit .env:
# SPARK_WORKER_CORES=4
# SPARK_WORKER_MEMORY=4g
# Then restart: docker-compose down && docker-compose up -d
```

### Task 5: Manually Trigger a DAG

**Via Airflow UI**:

1. http://localhost:8080
2. Find your DAG
3. Click ▶️ button
4. (Optional) Set run ID or parameters

**Via REST API**:

```powershell
$dag_id = "fintech_fraud_pipeline_v4"
$run_id = "manual_$(Get-Date -Format 'yyyyMMddHHmmss')"

curl -X POST `
  -H "Content-Type: application/json" `
  -d "{`"dag_run_id`": `"$run_id`"}" `
  -u admin:admin `
  http://localhost:8080/api/v1/dags/$dag_id/dagRuns
```

---

## Troubleshooting

### Problem 1: Services Don't Start

**Symptoms**: `docker-compose up` hangs or exits with error

**Solutions**:

```powershell
# Check Docker daemon status
docker ps

# Rebuild images from scratch
docker-compose down -v
docker system prune -a
docker-compose up -d --build

# Check logs
docker-compose logs

# Free up disk space if needed
docker system prune
```

### Problem 2: Airflow DAG Not Visible

**Symptoms**: DAG doesn't appear in Airflow UI after adding file

**Solutions**:

```powershell
# Check DAG file for syntax errors
docker exec airflow-webserver python -m py_compile \
  /opt/airflow/dags/fraud_pipeline_dag.py

# Check airflow-init completed
docker-compose logs airflow-init

# Restart scheduler
docker-compose restart airflow-scheduler

# View DAG parsing errors
docker-compose logs airflow-scheduler | grep -i "error\|exception"
```

### Problem 3: Spark Job Fails with S3A Error

**Symptoms**: "NumberFormatException" or connection timeout

**Solutions**:

```powershell
# Verify MinIO is running and healthy
docker-compose ps minio
curl http://localhost:9000/minio/health/live

# Check Spark logs for detailed error
docker-compose logs spark-master | grep -i "s3a\|exception"

# Verify network connectivity
docker network inspect spark-minio-network

# Restart Spark
docker-compose restart spark-master spark-worker
```

### Problem 4: File Not Found Error During Ingest

**Symptoms**: "FileNotFoundError" in ingest_to_minio task

**Solutions**:

```powershell
# Verify file exists on host
ls include/data/paysim/raw/paysim_day1.csv

# Verify file is mounted in Airflow container
docker exec airflow-webserver ls /opt/airflow/include/data/paysim/raw/

# Check docker-compose.yml volume mounts for Airflow services
# Should have: ./include:/opt/airflow/include

# Recreate container with fresh mounts
docker-compose down
docker-compose up -d
```

### Problem 5: Snowflake Connection Fails

**Symptoms**: Spark writes to MinIO OK, but Snowflake write fails

**Solutions**:

```powershell
# Verify Snowflake credentials
echo $env:SNOWFLAKE_ACCOUNT
echo $env:SNOWFLAKE_USER

# Check Snowflake account URL format (should be account ID, not full URL)
# Correct: myaccount
# Incorrect: myaccount.snowflakecomputing.com

# Test connection manually
docker exec spark-master snowsql \
  -a $env:SNOWFLAKE_ACCOUNT \
  -u $env:SNOWFLAKE_USER \
  -d $env:SNOWFLAKE_DB

# View Spark error logs
docker logs spark-master | tail -100 | grep -i snowflake
```

### Problem 6: Out of Memory / Crashes

**Symptoms**: Containers crash with OOMKilled, tasks timeout

**Solutions**:

```powershell
# Monitor resource usage
docker stats

# Increase Docker memory allocation (in Docker Desktop settings)
# Windows/Mac: Docker Desktop → Preferences → Resources → Memory

# Or scale back workers
docker-compose down
# Edit .env: reduce SPARK_WORKER_MEMORY, reduce --scale

# Or increase swap
docker-compose up -d --scale spark-worker=1 # Fewer workers

# Monitor again
docker stats
```

### Problem 7: Network Issues Between Services

**Symptoms**: "Connection refused", services can't communicate

**Solutions**:

```powershell
# Check Docker network
docker network ls
docker network inspect spark-minio-network

# All services should be on the same network
docker-compose ps

# Restart networking
docker-compose down
docker-compose up -d

# Test service-to-service connectivity
docker exec airflow-webserver curl http://minio:9000/minio/health/live
docker exec spark-master curl http://minio:9000/minio/health/live
```

---

## Performance Tips

### 1. Optimize Spark Configuration

In `dags/fraud_pipeline_dag.py`, adjust:

```python
SparkSubmitOperator(
    task_id='process_with_spark',
    ...
    conf={
        'spark.sql.shuffle.partitions': '100',  # Tune for data size
        'spark.executor.cores': '4',
        'spark.executor.memory': '4g',
        'spark.driver.memory': '2g',
    }
)
```

### 2. Increase Parallelism

```env
# In .env
SPARK_WORKER_CORES=4
SPARK_WORKER_MEMORY=4g

# Then scale
docker-compose up -d --scale spark-worker=3
```

### 3. Use Appropriate Data Partitioning

In Spark jobs, partition data for better performance:

```python
df.coalesce(50)  # Reduce to 50 partitions
# or
df.repartition(100)  # Increase to 100 partitions
```

### 4. Monitor Resource Usage

```powershell
# Real-time stats
docker stats

# Historical logs
docker-compose logs airflow-scheduler
docker logs spark-master
```

---

## Cleanup & Maintenance

### Stop All Services

```powershell
./stop-services.sh
# or
docker-compose down
```

### Remove All Data (Fresh Start)

```powershell
docker-compose down -v
# This removes all volumes (MinIO data, Postgres DB, Spark logs)
```

### Clean Docker System

```powershell
docker system prune -a  # Remove unused images, containers, networks
docker volume prune      # Remove unused volumes
```

### View Disk Usage

```powershell
docker system df
```

---

## Useful Commands Reference

```powershell
# Stack management
docker-compose up -d --build          # Start with rebuild
docker-compose down -v                # Stop and remove volumes
docker-compose ps                     # View service status
docker-compose logs -f                # Stream all logs
docker-compose logs -f airflow-scheduler  # Specific service

# Container management
docker exec -it spark-master bash     # Access container shell
docker logs spark-master              # View container logs
docker stats                          # Resource usage

# Network debugging
docker network ls                     # List networks
docker network inspect spark-minio-network  # Inspect network

# Scaling
docker-compose up -d --scale spark-worker=3  # Add workers

# Cleanup
docker system prune -a                # Remove all unused resources
docker volume prune                   # Remove unused volumes
```

---

## Next Steps

1. **Add Your Own Data**: Place CSV files in `include/data/paysim/raw/`
2. **Create New DAGs**: Add pipelines in `dags/` directory
3. **Deploy to Production**: Consider cloud options (AWS MWAA, GCP Composer, Azure Synapse)
4. **Set Up Monitoring**: Add Prometheus + Grafana for metrics
5. **Configure Alerts**: Set email/Slack notifications for failures

---

## Additional Resources

- **Airflow Docs**: https://airflow.apache.org/docs/
- **Spark Docs**: https://spark.apache.org/docs/latest/
- **MinIO Docs**: https://docs.min.io/
- **Docker Docs**: https://docs.docker.com/
- **PaySim Dataset**: https://www.kaggle.com/datasets/ealaxi/paysim1

---

**Last Updated**: November 24, 2025  
**Status**: Production Ready  
**Support**: Check logs first, then consult documentation

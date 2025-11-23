# Spark + MinIO + Airflow Setup Guide

## Overview

This repository provides a local development stack for a Spark + MinIO data pipeline orchestrated by Airflow. All services run as Docker containers and are attached to a single Docker network so Airflow can reach MinIO and Spark by service name.

## Architecture

```
┌─────────────────────┐         ┌──────────────────────┐
│   Airflow (Docker)  │ ──────> │  MinIO & Spark       │
│   Port: 8080        │         │  Ports: 9000-9001,   │
└─────────────────────┘         │  7077, 8088-8089     │
                                └──────────────────────┘
```

## Quick Start

### 1. Start the full local stack

```powershell
# From project root
./start-services.sh

# Wait for services to initialize
sleep 10

# Verify services are running
docker-compose ps
```

### 2. Access the UIs

- Airflow Web UI: http://localhost:8080 (admin/admin created by init step)
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- Spark Master UI: http://localhost:8088
- Spark Worker UI: http://localhost:8089

### 3. Run helper scripts from Airflow container

```powershell
docker exec -it airflow-webserver bash
python /opt/airflow/include/upload_test_data.py
```

### 4. Scale Spark workers

```powershell
docker-compose up -d --scale spark-worker=3
```

## File Structure

```
.
├── docker-compose.yml            # Unified compose for local dev
├── airflow/                      # Airflow Dockerfile and image context
├── dags/                         # Airflow DAGs
├── spark/                        # Spark Dockerfile and image context
├── spark-jobs/                   # PySpark job scripts
├── include/                      # Helper scripts (upload_test_data.py)
└── start-services.sh / stop-services.sh
```

## Troubleshooting

- If Airflow cannot reach MinIO or Spark, ensure all services are running and inspect the Docker network:

```powershell
docker network ls
docker network inspect spark-minio-network
```

- To view logs:

```powershell
docker-compose logs -f airflow-webserver
docker logs spark-master
docker logs minio
```

## Cleanup

```powershell
./stop-services.sh
docker-compose down -v
```

## Notes

- This repo intentionally runs Airflow locally via Docker Compose for development ease. For production deployments, consider using a managed Airflow service or Kubernetes-based deployments and avoid mounting the Docker socket into Airflow for security.

# Spark + MinIO + Airflow Setup Guide

## Overview

This repository provides a local development stack for a Spark + MinIO data pipeline orchestrated by Airflow. All services run as Docker containers and are attached to a single Docker network so Airflow can reach MinIO and Spark by service name.

## Architecture

```
┌─────────────────────┐         ┌──────────────────────┐
│   Airflow (Docker)  │ ──────> │  MinIO & Spark       │
│   Port: 8080        │         │  Ports: 9000-9001,   │
└─────────────────────┘         │  7077, 8088-8089     │
                                └──────────────────────┘
```

## Quick Start

### 1. Start the full local stack

```powershell
# From project root
./start-services.sh

# Wait for services to initialize
sleep 10

# Verify services are running
docker-compose ps
```

### 2. Access the UIs

- Airflow Web UI: http://localhost:8080 (admin/admin created by init step)
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- Spark Master UI: http://localhost:8088
- Spark Worker UI: http://localhost:8089

### 3. Run helper scripts from Airflow container

```powershell
docker exec -it airflow-webserver bash
python /opt/airflow/include/upload_test_data.py
```

### 4. Scale Spark workers

```powershell
docker-compose up -d --scale spark-worker=3
```

## File Structure

```
.
├── docker-compose.yml            # Unified compose for local dev
├── airflow/                      # Airflow Dockerfile and image context
├── dags/                         # Airflow DAGs
├── spark/                        # Spark Dockerfile and image context
├── spark-jobs/                   # PySpark job scripts
├── include/                      # Helper scripts (upload_test_data.py)
└── start-services.sh / stop-services.sh
```

## Troubleshooting

- If Airflow cannot reach MinIO or Spark, ensure all services are running and inspect the Docker network:

```powershell
docker network ls
docker network inspect spark-minio-network
```

- To view logs:

```powershell
docker-compose logs -f airflow-webserver
docker logs spark-master
docker logs minio
```

## Cleanup

```powershell
./stop-services.sh
docker-compose down -v
```

## Notes

- This repo intentionally runs Airflow locally via Docker Compose for development ease. For production deployments, consider using a managed Airflow service or Kubernetes-based deployments and avoid mounting the Docker socket into Airflow for security.

# Spark + MinIO + Airflow Setup Guide

## Overview

This repository provides a local development stack for a Spark + MinIO data pipeline orchestrated by Airflow. All services run as Docker containers and are wired on a single Docker network so Airflow can reach MinIO and Spark by service name.

## Architecture

```
┌─────────────────────┐         ┌──────────────────────┐
│   Airflow (Docker)  │ ──────> │  MinIO & Spark       │
│   Port: 8080        │         │  Ports: 9000-9001,   │
└─────────────────────┘         │  7077, 8088-8089     │
                                └──────────────────────┘
```

## Quick Start

### 1. Start the full local stack

```powershell
# Start MinIO, Spark, Postgres, and Airflow
./start-services.sh

# Wait for services to initialize
sleep 10

# Verify services are running
docker-compose ps
```

### Alternative: Start subsets

If you prefer to start only specific services, you can start them individually. Example:

```powershell
docker-compose up -d minio spark-master spark-worker
```

### 2. Use Airflow

1. Open Airflow UI: http://localhost:8080
2. Find the DAG `spark_minio_processing`
3. Toggle it ON and trigger it manually

The DAGs and helper scripts can also be run from inside the `airflow-webserver` container if needed.

### 3. Exec into Airflow to run helpers

```powershell
# Exec into the airflow-webserver container
docker exec -it airflow-webserver bash
python /opt/airflow/include/upload_test_data.py
```

## Service URLs

| Service         | URL                   | Credentials             |
| --------------- | --------------------- | ----------------------- |
| Airflow UI      | http://localhost:8080 | admin / admin           |
| MinIO Console   | http://localhost:9001 | minioadmin / minioadmin |
| MinIO API       | http://localhost:9000 | minioadmin / minioadmin |
| Spark Master UI | http://localhost:8088 | -                       |
| Spark Worker UI | http://localhost:8089 | -                       |

## File Structure

```
.
├── docker-compose.yml            # Unified compose for local dev
├── airflow/                      # Airflow Dockerfile and image context
├── dags/                         # Airflow DAGs
├── spark/                        # Spark Dockerfile and image context
├── spark-jobs/                   # PySpark job scripts
├── include/                      # Helper scripts (upload_test_data.py)
└── start-services.sh / stop-services.sh
```

## Cleanup

### Stop all services

```powershell
./stop-services.sh
```

### Remove volumes and networks

```powershell
# Stop services first
./stop-services.sh

# Remove volumes and networks
docker-compose down -v
```

## Service URLs

Once all services are running, access them at:

| Service         | URL                   | Credentials             |
| --------------- | --------------------- | ----------------------- |
| Airflow UI      | http://localhost:8080 | admin / admin           |
| MinIO Console   | http://localhost:9001 | minioadmin / minioadmin |
| MinIO API       | http://localhost:9000 | minioadmin / minioadmin |
| Spark Master UI | http://localhost:8088 | -                       |
| Spark Worker UI | http://localhost:8089 | -                       |

## Running the Data Pipeline

### 1. Verify services are running

Check that all services are accessible via their web interfaces.

### 2. Trigger the DAG

1. Go to Airflow UI: http://localhost:8080
2. Find the DAG: `spark_minio_processing`
3. Toggle it ON
4. Click the "Play" button to trigger manually

### 3. Monitor the pipeline

The DAG will:

## Overview

This setup provides a complete data processing pipeline with:

- **Apache Airflow** for orchestration (running as a local Docker service)
- **Apache Spark** for distributed data processing (separate Docker containers)
- **MinIO** for S3-compatible object storage (separate Docker container)

4. **Verify Output** - Check processed data in output-bucket

### 4. View results

│ (Local Docker) │ ──────> │ (Separate Docker) │

- Check MinIO Console to see input and output files
- View Spark job execution in Spark Master UI
- Monitor task logs in Airflow UI

## File Structure

````
.
├── docker-compose.minio-spark.yml  # MinIO & Spark services
├── spark/
│   └── Dockerfile                   # Spark container with dependencies
├── spark-jobs/
│   └── process_data.py             # PySpark processing script
├── dags/
│   └── spark_minio_processing_dag.py  # Airflow DAG
├── include/
### 2. Start Airflow (already part of the full stack above)
1. Go to Airflow UI: http://localhost:8080
2. Find the DAG: `spark_minio_processing`
3. Toggle it ON
4. Click the "Play" button to trigger manually

## Data Processing Details

The PySpark job (`spark-jobs/process_data.py`):
- Reads CSV/JSON data from MinIO input-bucket
- Adds metadata columns (timestamp, job name)
- Transforms string columns to uppercase
- Calculates derived fields
- Writes processed data to output-bucket
### Alternative: Start subsets
If you prefer to start only specific services, use docker-compose with the older Compose file names or service names. For example:

```powershell
docker-compose up -d minio spark-master spark-worker
````

## Customization

### Via Python script

From inside the Airflow container (or any environment that can reach MinIO):

```bash
# Exec into the airflow-webserver container
docker exec -it airflow-webserver bash
python /opt/airflow/include/upload_test_data.py
```

1. Create new `.py` files in `spark-jobs/`
2. Update the DAG to call your new script

### Change bucket names

Update bucket names in:

- `docker-compose.minio-spark.yml` (minio-init service)
- `dags/spark_minio_processing_dag.py`

### Adjust Spark resources

Edit `docker-compose.minio-spark.yml`:

```yaml
SPARK_WORKER_CORES: 2 # CPU cores
SPARK_WORKER_MEMORY: 2g # Memory allocation
```

## Uploading Your Own Data

### Via MinIO Console

1. Go to http://localhost:9001

# Cleanup

### Stop all services

```powershell
./stop-services.sh
```

### Remove all data and volumes

```powershell
# Stop services first
./stop-services.sh

# Remove volumes and networks
docker-compose down -v
```

2. Login with minioadmin/minioadmin
3. Navigate to `input-bucket`
4. Upload your CSV or JSON files

### Via Python script

```bash
# Exec into the airflow-webserver container
docker exec -it airflow-webserver bash
python /opt/airflow/include/upload_test_data.py
```

### Via AWS CLI

```bash
# Configure AWS CLI for MinIO
aws configure set aws_access_key_id minioadmin
aws configure set aws_secret_access_key minioadmin

# Upload file
aws --endpoint-url http://localhost:9000 \
    s3 cp yourfile.csv s3://input-bucket/
```

## Troubleshooting

### MinIO Connection Issues

```bash
# Check MinIO is running
docker ps | grep minio

# View MinIO logs
docker logs minio

# Test connection
curl http://localhost:9000/minio/health/live
```

### Spark Issues

```bash
# Check Spark containers
docker ps | grep spark

# View Spark Master logs
docker logs spark-master

# View Spark Worker logs
docker logs spark-worker

# Check if worker is registered
curl http://localhost:8088
```

### Airflow Task Failures

1. Click on the failed task in Airflow UI
2. Select "Log" to view detailed error messages
3. Check if external services are accessible

### Network Issues

If Airflow can't reach MinIO/Spark:

```bash
# Check Docker networks
docker network ls

# Inspect network
docker network inspect spark-minio-network

# Restart services
./stop-services.sh
./start-services.sh
```

## Cleanup

### Stop all services

```bash
./stop-services.sh
```

### Remove all data and volumes

```bash
# Stop services first
./stop-services.sh

# Remove MinIO and Spark volumes
docker-compose -f docker-compose.minio-spark.yml down -v

# Clean Airflow
docker-compose down -v
```

## Performance Tuning

### Spark Configuration

Edit spark-submit parameters in the DAG:

- `spark.executor.memory`: Memory per executor
- `spark.executor.cores`: Cores per executor
- `spark.sql.shuffle.partitions`: Number of partitions for shuffles

### MinIO Performance

- Use multiple MinIO nodes for production
- Configure appropriate storage backend
- Tune connection pool sizes in Spark

## Next Steps

1. **Add more workers**: Scale Spark by adding more worker containers
2. **Implement partitioning**: Partition data by date/category for better performance
3. **Add data validation**: Implement schema validation in Spark jobs
4. **Create more DAGs**: Build additional pipelines for different data sources
5. **Set up monitoring**: Add Prometheus/Grafana for metrics

## Resources

- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [MinIO Documentation](https://docs.min.io/)
  -- [Airflow Documentation](https://airflow.apache.org/docs/)
- [Airflow Documentation](https://airflow.apache.org/docs/)

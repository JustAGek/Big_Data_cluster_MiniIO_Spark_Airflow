#!/bin/bash

# Start the combined stack (MinIO, Spark, Postgres, Airflow)
echo "🚀 Starting MinIO, Spark and Airflow services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready (give it ~15s)..."
sleep 15

echo ""
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "✅ Services started (or starting)."
echo ""
echo "📌 Service URLs:"
echo "   Airflow UI:        http://localhost:8080 (admin/admin)"
echo "   MinIO Console:     http://localhost:9001 (minioadmin/minioadmin)"
echo "   MinIO API:         http://localhost:9000"
echo "   Spark Master UI:   http://localhost:8088"
echo "   Spark Worker UI:   http://localhost:8089"
echo ""
echo "To scale Spark workers (example: 3 workers):"
echo "  docker-compose up -d --scale spark-worker=3"
echo ""
echo "Notes:" 
echo " - Airflow DAGs are in ./dags; the example DAG submits Spark jobs to the local Spark master."
echo " - The DAG has been updated to use service hostnames (minio, spark-master)."
#!/bin/bash

# Stop the combined docker-compose stack
echo "🛑 Stopping Airflow, MinIO, and Spark services..."
docker-compose down

echo ""
echo "✅ All services stopped successfully!"
#!/usr/bin/env python3
"""
Helper script to upload test data to MinIO input bucket.
Can be run manually or imported into DAGs.
"""

import boto3
from botocore.client import Config
import pandas as pd
import json
import os
from datetime import datetime

def get_minio_client():
    """Get MinIO S3 client"""
    return boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://minio:9000'),
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )

def create_sample_csv_data():
    """Create sample CSV data"""
    return pd.DataFrame({
        'id': range(1, 101),
        'name': [f'Customer_{i}' for i in range(1, 101)],
        'age': [20 + (i % 50) for i in range(100)],
        'city': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'] * 20,
        'purchase_amount': [100 + (i * 10) for i in range(100)],
        'purchase_date': pd.date_range(start='2024-01-01', periods=100, freq='D').strftime('%Y-%m-%d').tolist(),
        'category': ['Electronics', 'Clothing', 'Food', 'Books', 'Sports'] * 20,
        'is_premium': [i % 3 == 0 for i in range(100)]
    })

def create_sample_json_data():
    """Create sample JSON data"""
    data = []
    for i in range(1, 51):
        data.append({
            'transaction_id': f'TXN{i:05d}',
            'timestamp': datetime.now().isoformat(),
            'user': {
                'id': f'USER{i:03d}',
                'name': f'User_{i}',
                'email': f'user{i}@example.com'
            },
            'product': {
                'id': f'PROD{(i % 10) + 1:03d}',
                'name': f'Product_{(i % 10) + 1}',
                'price': 50 + (i * 5)
            },
            'quantity': (i % 5) + 1,
            'total': (50 + (i * 5)) * ((i % 5) + 1)
        })
    return data

def upload_csv_to_minio(s3_client, bucket='input-bucket', filename='sample_data.csv'):
    """Upload CSV data to MinIO"""
    df = create_sample_csv_data()
    csv_string = df.to_csv(index=False)

    s3_client.put_object(
        Bucket=bucket,
        Key=filename,
        Body=csv_string.encode('utf-8')
    )
    print(f"Uploaded CSV: {filename} to {bucket}")
    return filename

def upload_json_to_minio(s3_client, bucket='input-bucket', filename='sample_data.json'):
    """Upload JSON data to MinIO"""
    data = create_sample_json_data()
    json_string = json.dumps(data, indent=2)

    s3_client.put_object(
        Bucket=bucket,
        Key=filename,
        Body=json_string.encode('utf-8')
    )
    print(f"Uploaded JSON: {filename} to {bucket}")
    return filename

def list_bucket_contents(s3_client, bucket):
    """List contents of a MinIO bucket"""
    try:
        response = s3_client.list_objects_v2(Bucket=bucket)
        if 'Contents' in response:
            print(f"\nContents of bucket '{bucket}':")
            for obj in response['Contents']:
                print(f"  - {obj['Key']} (Size: {obj['Size']} bytes, Modified: {obj['LastModified']})")
        else:
            print(f"Bucket '{bucket}' is empty")
    except Exception as e:
        print(f"Error listing bucket {bucket}: {str(e)}")

def main():
    """Main function to upload test data"""
    print("Uploading test data to MinIO...")

    try:
        # Get MinIO client
        s3_client = get_minio_client()

        # Create buckets if they don't exist
        buckets = ['input-bucket', 'output-bucket']
        existing_buckets = [b['Name'] for b in s3_client.list_buckets()['Buckets']]

        for bucket in buckets:
            if bucket not in existing_buckets:
                s3_client.create_bucket(Bucket=bucket)
                print(f"Created bucket: {bucket}")
            else:
                print(f"Bucket already exists: {bucket}")

        # Upload sample data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Upload CSV data
        csv_file = upload_csv_to_minio(
            s3_client,
            filename=f'sales_data_{timestamp}.csv'
        )

        # Upload JSON data
        json_file = upload_json_to_minio(
            s3_client,
            filename=f'transactions_{timestamp}.json'
        )

        # List bucket contents
        list_bucket_contents(s3_client, 'input-bucket')
        list_bucket_contents(s3_client, 'output-bucket')

        print(f"\nTest data uploaded successfully!")
        print(f"CSV file: {csv_file}")
        print(f"JSON file: {json_file}")

    except Exception as e:
        print(f"Error: {str(e)}")
        return False

    return True

if __name__ == "__main__":
    main()
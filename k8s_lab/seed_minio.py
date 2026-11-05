import os
import boto3
from botocore.config import Config

SRC_ENDPOINT = os.environ.get("SRC_ENDPOINT", "http://localhost:9000")
SRC_KEY = os.environ.get("SRC_KEY", "admin")
SRC_SECRET = os.environ.get("SRC_SECRET", "password123")
DST_ENDPOINT = os.environ.get("DST_ENDPOINT", "http://localhost:30900")
DST_KEY = os.environ.get("DST_KEY", "minioadmin")
DST_SECRET = os.environ.get("DST_SECRET", "minioadmin")
BUCKET = os.environ.get("BUCKET", "vacancies-dataset")

src = boto3.client("s3", endpoint_url=SRC_ENDPOINT, aws_access_key_id=SRC_KEY,
                   aws_secret_access_key=SRC_SECRET,
                   config=Config(signature_version="s3v4", connect_timeout=5, read_timeout=30, retries={"max_attempts": 3}))
dst = boto3.client("s3", endpoint_url=DST_ENDPOINT, aws_access_key_id=DST_KEY,
                   aws_secret_access_key=DST_SECRET,
                   config=Config(signature_version="s3v4", connect_timeout=5, read_timeout=30, retries={"max_attempts": 3}))

try:
    dst.head_bucket(Bucket=BUCKET)
    print("Bucket exists:", BUCKET)
except Exception:
    dst.create_bucket(Bucket=BUCKET)
    print("Bucket created:", BUCKET)

paginator = src.get_paginator("list_objects_v2")
count = 0
for page in paginator.paginate(Bucket=BUCKET):
    for obj in page.get("Contents", []):
        key = obj["Key"]
        if key.startswith("partials/"):
            continue
        body = src.get_object(Bucket=BUCKET, Key=key)["Body"].read()
        dst.put_object(Bucket=BUCKET, Key=key, Body=body)
        count += 1
        if count % 100 == 0:
            print("Copied", count)

print("Transfer finished:", count)
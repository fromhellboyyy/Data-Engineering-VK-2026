import os
import json
from collections import Counter

import boto3
from botocore.config import Config

SEP = ""

S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://localhost:30900")
S3_BUCKET = os.environ.get("S3_BUCKET", "vacancies-dataset")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "minioadmin")
PARTIAL_PREFIX = os.environ.get("PARTIAL_PREFIX", "partials/")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version="s3v4", connect_timeout=5, read_timeout=10, retries={"max_attempts": 3}),
)

total = Counter()

resp = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=PARTIAL_PREFIX)
for obj in resp.get("Contents", []):
    key = obj["Key"]
    body = s3.get_object(Bucket=S3_BUCKET, Key=key)["Body"].read().decode("utf-8")
    data = json.loads(body)
    for encoded_pair, count in data.items():
        pair = tuple(encoded_pair.split(SEP))
        total[pair] += count

items = sorted(total.items(), key=lambda x: (-x[1], " + ".join(sorted(x[0]))))

print("UNIQUE_PAIRS", len(total))
for i, (pair, count) in enumerate(items[:10], 1):
    print(i, " + ".join(sorted(pair)), count)
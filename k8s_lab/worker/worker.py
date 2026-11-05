import os
import json
import resource
import itertools
from collections import Counter

import boto3
from botocore.config import Config

SEP = ""

S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://minio:9000")
S3_BUCKET = os.environ.get("S3_BUCKET", "vacancies-dataset")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "minioadmin")

SHARD_INDEX = int(os.environ.get("JOB_COMPLETION_INDEX", os.environ.get("SHARD_INDEX", "0")))
SHARD_COUNT = int(os.environ.get("SHARD_COUNT", "1"))
LIST_PATH = os.environ.get("LIST_PATH", "/etc/filelist/list.txt")
PARTIAL_PREFIX = os.environ.get("PARTIAL_PREFIX", "partials/")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version="s3v4", connect_timeout=5, read_timeout=10, retries={"max_attempts": 3}),
)

def load_files():
    with open(LIST_PATH, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def pairs_of(vacancy):
    skills = vacancy.get("key_skills") or []
    skills = sorted({str(s).strip() for s in skills if str(s).strip()})
    return [tuple(p) for p in itertools.combinations(skills, 2)]

def serialize(counter):
    return {SEP.join(pair): count for pair, count in counter.items()}

def main():
    files = load_files()
    selected = files[SHARD_INDEX::SHARD_COUNT]
    counter = Counter()

    for filename in selected:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=filename)
        vacancy = json.loads(obj["Body"].read().decode("utf-8"))
        for pair in pairs_of(vacancy):
            counter[pair] += 1

    peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    print(f"SHARD={SHARD_INDEX} FILES={len(selected)} PAIRS_UNIQUE={len(counter)} PEAK_RSS_MB={peak_mb:.2f}")

    key = f"{PARTIAL_PREFIX}pairs-{SHARD_INDEX:03d}.json"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(serialize(counter), ensure_ascii=False).encode("utf-8"),
    )
    print(f"PARTIAL_UPLOADED={key}")

if __name__ == "__main__":
    main()
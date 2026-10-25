import os, sys, json, time, threading, itertools, logging
from collections import Counter
from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError, BadVersionError, ConnectionLoss, SessionExpiredError
import boto3
from botocore.config import Config

ZK_HOSTS = os.environ.get("ZK_HOSTS", "zoo1:2181,zoo2:2181,zoo3:2181")
S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://host.docker.internal:9000")
S3_BUCKET = os.environ.get("S3_BUCKET", "vacancies-dataset")
COORD_ID = os.environ.get("COORD_ID", "coord?")
FENCING = os.environ.get("FENCING", "0") == "1"
LOG_TAG = os.environ.get("LOG_TAG", "run")
SESSION_TO = int(os.environ.get("SESSION_TIMEOUT", "10"))
SLEEP_PER = float(os.environ.get("SLEEP_PER", "1.0"))
CKPT_EVERY = int(os.environ.get("CKPT_EVERY", "5"))
SEP = ""

LEADER_P = "/zk_lab/leader"
CKPT_P = "/zk_lab/checkpoint"
RESULT_P = "/zk_lab/result"
LIST_FILE = "/data/csharp_files_list.txt"
LOG_DIR = "/app/logs"

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(name)s] %(message)s", datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout),
              logging.FileHandler(os.path.join(LOG_DIR, f"{COORD_ID}_{LOG_TAG}.log"), encoding="utf-8")])
log = logging.getLogger(COORD_ID)

s3 = boto3.client("s3", endpoint_url=S3_ENDPOINT, aws_access_key_id="admin",
                  aws_secret_access_key="password123",
                  config=Config(connect_timeout=5, read_timeout=10, retries={"max_attempts": 3}))

def ev(msg, **kw):
    kw["ts"] = round(time.time(), 3)
    log.info("EVENT=%s %s", msg, " ".join(f"{k}={v}" for k, v in kw.items()))

def load_files():
    with open(LIST_FILE, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]

def fetch_vacancy(fn):
    resp = s3.get_object(Bucket=S3_BUCKET, Key=fn)
    return json.loads(resp["Body"].read().decode("utf-8"))

def pairs_of(vac):
    skills = vac.get("key_skills") or []
    skills = sorted({str(s).strip() for s in skills if str(s).strip()})
    return [tuple(p) for p in itertools.combinations(skills, 2)]

def ser(c): return {SEP.join(k): v for k, v in c.items()}
def deser(d): return Counter({tuple(k.split(SEP)): v for k, v in d.items()})

def safe_set(client, path, value, version=None, retries=30):
    for _ in range(retries):
        try:
            if version is None:
                return client.set(path, value)
            return client.set(path, value, version=version)
        except (ConnectionLoss, SessionExpiredError):
            time.sleep(1.0)
    raise RuntimeError("safe_set failed")

def election(client, my_id):
    while True:
        try:
            client.create(LEADER_P, my_id.encode(), ephemeral=True)
            return
        except NodeExistsError:
            gate = threading.Event()
            def cb(_e): gate.set()
            st = client.exists(LEADER_P, watch=cb)
            if st is None:
                continue
            gate.wait()

def compute(client, resume_idx, counter):
    files = load_files()
    ev("compute_started", files=len(files), resume_idx=resume_idx)
    for i in range(resume_idx, len(files)):
        vac = fetch_vacancy(files[i])
        for p in pairs_of(vac):
            counter[p] += 1
        if (i + 1) % CKPT_EVERY == 0 or i == len(files) - 1:
            client.set(CKPT_P, json.dumps({"idx": i + 1, "pairs": ser(counter)}).encode())
        time.sleep(SLEEP_PER)
    return counter

def publish(client, counter, fence_version):
    payload = {"pairs_unique": len(counter),
               "top3": [[list(k), v] for k, v in counter.most_common(3)],
               "leader": COORD_ID, "fencing": FENCING, "ts": round(time.time(), 3)}
    body = json.dumps(payload, ensure_ascii=False).encode()
    if FENCING:
        try:
            st = safe_set(client, RESULT_P, body, version=fence_version)
            ev("published", mode="fence", new_version=st.version, pairs_unique=len(counter))
        except BadVersionError:
            ev("rejected", mode="fence", err="BadVersionError", expected_version=fence_version, pairs_unique=len(counter))
    else:
        st = safe_set(client, RESULT_P, body)
        ev("published", mode="nofence", new_version=st.version, pairs_unique=len(counter))

def main():
    client = KazooClient(hosts=ZK_HOSTS, timeout=SESSION_TO)
    client.start()
    client.ensure_path("/zk_lab")
    client.ensure_path(CKPT_P)
    client.ensure_path(RESULT_P)
    ev("ready", fencing=FENCING, session_timeout=SESSION_TO)
    election(client, COORD_ID)
    _, st = client.get(RESULT_P)
    fence_version = st.version
    ev("became_leader", fence_version=fence_version)
    data, _ = client.get(CKPT_P)
    if data:
        cp = json.loads(data.decode())
        resume_idx, counter = cp["idx"], deser(cp["pairs"])
        ev("resumed_from_checkpoint", idx=resume_idx)
    else:
        resume_idx, counter = 0, Counter()
        ev("fresh_start", idx=0)
    counter = compute(client, resume_idx, counter)
    publish(client, counter, fence_version)
    ev("done")
    client.stop()

if __name__ == "__main__":
    main()
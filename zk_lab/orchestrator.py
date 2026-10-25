import subprocess, time, sys, os

MODE = sys.argv[1] if len(sys.argv) > 1 else "nofence"
FENCING = "1" if MODE == "fence" else "0"
LOG_TAG = MODE
PAUSE_AFTER_START = 20
SESSION_TO = 10

BASE = os.path.dirname(os.path.abspath(__file__))
LIST_F = os.path.join(BASE, "..", "rustfs_lab", "csharp_files_list.txt")
LOGS_DIR = os.path.join(BASE, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

ENV = {"ZK_HOSTS": "zoo1:2181,zoo2:2181,zoo3:2181",
       "S3_ENDPOINT": "http://host.docker.internal:9000",
       "S3_BUCKET": "vacancies-dataset",
       "FENCING": FENCING, "LOG_TAG": LOG_TAG,
       "SESSION_TIMEOUT": str(SESSION_TO), "SLEEP_PER": "1.0"}

def sh(*a): return subprocess.run(a, capture_output=True, text=True)
def logs(name):
    r = sh("docker","logs",name); return (r.stdout or "")+(r.stderr or "")
def tail(text, n=40):
    lines = text.splitlines(); return "\n".join(lines[-n:])
def wait_for(name, needle, timeout=180):
    t0=time.time()
    while time.time()-t0 < timeout:
        out = logs(name)
        if needle in out: return time.time()
        time.sleep(1.0)
    print(f"!!! Таймаут '{needle}' в {name}. Хвост логов:")
    print(tail(logs(name)))
    raise TimeoutError(f"{name}: не дождались '{needle}'")

def up(name):
    e = dict(ENV); e["COORD_ID"] = name
    env_args = sum([["-e", f"{k}={v}"] for k, v in e.items()], [])
    r = sh("docker","run","-d","--name",name,"--network","zknet",
              *env_args,
              "-v", LIST_F+":/data/csharp_files_list.txt:ro",
              "-v", LOGS_DIR+":/app/logs",
              "zk_lab-coordinator")
    if r.returncode != 0:
        print(f"!!! docker run {name}:\n{r.stderr}")
    return r

def rm(*names): sh("docker","rm","-f",*names)

def reset_zk():
    py = ("from kazoo.client import KazooClient;"
          "c=KazooClient(hosts='localhost:2181,localhost:2182,localhost:2183',timeout=10);c.start();"
          "import contextlib\n"
          "for p in ['/zk_lab/result','/zk_lab/checkpoint']:\n"
          "    with contextlib.suppress(Exception): c.delete(p, recursive=True)\n"
          "    c.ensure_path(p)\n"
          "c.stop()")
    r = sh("python","-c",py)
    if r.returncode != 0:
        print("reset_zk warn:", (r.stderr or "")[:300])

print(f"=== РЕЖИМ: {MODE} (FENCING={FENCING}) ===")
print("LIST_F =", LIST_F, "| существует:", os.path.isfile(LIST_F))
rm("coord1","coord2"); reset_zk()
up("coord1")
wait_for("coord1", "EVENT=compute_started")
print("coord1 начал расчёт; поднимаем coord2")
up("coord2")
print(f"ждём {PAUSE_AFTER_START}s до чекпоинта ~idx=20 ...")
time.sleep(PAUSE_AFTER_START)
t_pause = time.time()
sh("docker","pause","coord1"); print(f"[{t_pause:.3f}] PAUSE coord1")
t_became = wait_for("coord2", "EVENT=became_leader")
switch = t_became - t_pause
print(f"[{t_became:.3f}] coord2 became_leader; СМЕНА ЛИДЕРА = {switch:.2f} с")
print("ждём завершения расчёта coord2 ...")
wait_for("coord2", "EVENT=done", timeout=120)
print(f"[{time.time():.3f}] UNPAUSE coord1 (пауза {time.time()-t_pause:.1f}s)")
sh("docker","unpause","coord1")
print("ждём публикацию/отклонение coord1 ...")
wait_for("coord1", "EVENT=done", timeout=120)
time.sleep(2)
print("\n--- coord1 (stale лидер) ---"); print(logs("coord1"))
print("--- coord2 (запасной -> лидер) ---"); print(logs("coord2"))
print(f"\nИТОГ режим={MODE}: смена лидера {switch:.2f} с; логи в {LOGS_DIR}")
rm("coord1","coord2")
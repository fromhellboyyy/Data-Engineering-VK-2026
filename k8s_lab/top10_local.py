import sys
import json
import ast

SEP = ""
path = sys.argv[1] if len(sys.argv) > 1 else r"..\rustfs_lab\results\mapreduce_results.json"

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

pairs = data["pairs"]

def parse_key(key):
    if isinstance(key, (list, tuple)):
        return tuple(str(x).strip() for x in key)
    if SEP in key:
        return tuple(p.strip() for p in key.split(SEP))
    if " + " in key:
        return tuple(p.strip() for p in key.split(" + "))
    try:
        val = ast.literal_eval(key)
        if isinstance(val, (list, tuple)):
            return tuple(str(x).strip() for x in val)
    except Exception:
        pass
    return (key.strip(),)

items = []
for k, v in pairs.items():
    pair = tuple(sorted(parse_key(k)))
    items.append((pair, v))

items.sort(key=lambda x: (-x[1], " + ".join(x[0])))

print("UNIQUE_PAIRS", len(items))
for i, (pair, count) in enumerate(items[:10], 1):
    print(i, " + ".join(pair), count)
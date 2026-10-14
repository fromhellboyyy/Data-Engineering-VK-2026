import duckdb
import json
import pandas as pd
import itertools
import os

print("Анализ через DuckDB")

with open('csharp_files_list.txt', 'r', encoding='utf-8') as f:
    files = [line.strip() for line in f if line.strip()]

data = []
for filename in files:
    try:
        with open(f'json_files/{filename}', 'r', encoding='utf-8') as f:
            data.append(json.load(f))
    except Exception:
        pass

df = pd.DataFrame(data)
con = duckdb.connect()
con.execute("CREATE TABLE vacancies AS SELECT * FROM df")

singles_sql = """
    SELECT skill, COUNT(*) as count 
    FROM (SELECT UNNEST(key_skills) as skill FROM vacancies WHERE key_skills IS NOT NULL) 
    GROUP BY skill ORDER BY count DESC
"""
duckdb_singles = {str(row[0]).strip(): row[1] for row in con.execute(singles_sql).fetchall()}

pairs_data = []
triples_data = []

for row in con.execute("SELECT key_skills FROM vacancies WHERE key_skills IS NOT NULL").fetchall():
    skills = [str(s).strip() for s in row[0] if str(s).strip()]
    for pair in itertools.combinations(skills, 2):
        sorted_pair = sorted(pair)
        pairs_data.append({"combo": f"{sorted_pair[0]} + {sorted_pair[1]}"})
    for triple in itertools.combinations(skills, 3):
        sorted_triple = sorted(triple)
        triples_data.append({"combo": f"{sorted_triple[0]} + {sorted_triple[1]} + {sorted_triple[2]}"})

df_pairs = pd.DataFrame(pairs_data)
df_triples = pd.DataFrame(triples_data)

con.execute("CREATE TABLE pairs AS SELECT * FROM df_pairs")
con.execute("CREATE TABLE triples AS SELECT * FROM df_triples")

pairs_sql = "SELECT combo, COUNT(*) as count FROM pairs GROUP BY combo ORDER BY count DESC"
triples_sql = "SELECT combo, COUNT(*) as count FROM triples GROUP BY combo ORDER BY count DESC"

duckdb_pairs = {str(row[0]).strip(): row[1] for row in con.execute(pairs_sql).fetchall()}
duckdb_triples = {str(row[0]).strip(): row[1] for row in con.execute(triples_sql).fetchall()}

with open('results/mapreduce_results.json', 'r', encoding='utf-8') as f:
    mr_results = json.load(f)

def compare_dicts(d1, d2, name):
    if d1 == d2:
        print(f"{name}: Полное совпадение")
    else:
        print(f"{name}: Есть расхождения")
        diff = {k: (d1.get(k), d2.get(k)) for k in set(d1) | set(d2) if d1.get(k) != d2.get(k)}
        for k, v in list(diff.items())[:3]:
            print(f" '{k}': MapReduce={v[0]}, DuckDB={v[1]}")

compare_dicts(mr_results['singles'], duckdb_singles, "Одиночные навыки")
compare_dicts(mr_results['pairs'], duckdb_pairs, "Пары навыков")
compare_dicts(mr_results['triples'], duckdb_triples, "Тройки навыков")

os.makedirs('results', exist_ok=True)
with open('results/duckdb_results.json', 'w', encoding='utf-8') as f:
    json.dump({'singles': duckdb_singles, 'pairs': duckdb_pairs, 'triples': duckdb_triples}, f, ensure_ascii=False, indent=2)
print("Результаты DuckDB сохранены в results/duckdb_results.json")
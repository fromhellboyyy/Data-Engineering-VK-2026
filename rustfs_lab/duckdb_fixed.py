import duckdb, json, time, tracemalloc, itertools
import pandas as pd
import os
from collections import Counter

KEYWORDS = ['c#', '.net', 'c sharp', 'asp.net', 'entity framework',
            'wpf', 'xamarin', 'maui']

parts = []
for kw in KEYWORDS:
    parts.append("lower(name) LIKE '%" + kw + "%'")
    parts.append("lower(description) LIKE '%" + kw + "%'")
    parts.append("lower(array_to_string(key_skills, ' ')) LIKE '%" + kw + "%'")
WHERE_VAR = ' OR '.join(parts)

rows = []
for fn in os.listdir('json_files') if False else []:
    pass
import os
for fn in os.listdir('json_files'):
    if fn.endswith('.json'):
        with open('json_files/' + fn, 'r', encoding='utf-8') as f:
            rows.append(json.load(f))

df = pd.DataFrame(rows)
con = duckdb.connect()
con.execute('CREATE TABLE vacancies AS SELECT * FROM df')

cnt = con.execute('SELECT COUNT(*) FROM vacancies WHERE ' + WHERE_VAR).fetchone()[0]
print('Вакансий варианта по SQL-условию:', cnt)

con.execute('CREATE TABLE variant AS SELECT key_skills FROM vacancies WHERE ' + WHERE_VAR)
variant_skills = [r[0] for r in con.execute('SELECT key_skills FROM variant').fetchall()]

singles_sql = ('SELECT skill, COUNT(*) c FROM (SELECT UNNEST(key_skills) skill '
               'FROM variant WHERE key_skills IS NOT NULL) GROUP BY skill ORDER BY c DESC')

metrics = []
final = None
for attempt in range(3):
    tracemalloc.start()
    t0 = time.time()
    d_singles = {str(r[0]).strip(): r[1] for r in con.execute(singles_sql).fetchall()}
    pc, tc = Counter(), Counter()
    for ks in variant_skills:
        sk = [str(s).strip() for s in ks if str(s).strip()]
        for p in itertools.combinations(sk, 2):
            pc[tuple(sorted(p))] += 1
        for tr in itertools.combinations(sk, 3):
            tc[tuple(sorted(tr))] += 1
    d_pairs = {(a + ' + ' + b): c for (a, b), c in pc.items()}
    d_triples = {(a + ' + ' + b + ' + ' + c): n for (a, b, c), n in tc.items()}
    el = time.time() - t0
    cur, pk = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    metrics.append((el, pk / 1024 / 1024))
    final = (d_singles, d_pairs, d_triples)
    tt = round(el, 4); mm = round(pk / 1024 / 1024, 2)
    print('DuckDB попытка', attempt + 1, '| время сек:', tt, '| пик MB:', mm)

avg_t = round(sum(m[0] for m in metrics) / 3, 4)
avg_m = round(sum(m[1] for m in metrics) / 3, 2)
print('DuckDB среднее | время сек:', avg_t, '| пик MB:', avg_m)

with open('results/mapreduce_results.json', 'r', encoding='utf-8') as f:
    mr = json.load(f)
ds, dp, dt = final
print('Верификация singles:', ds == mr['singles'])
print('Верификация pairs:', dp == mr['pairs'])
print('Верификация triples:', dt == mr['triples'])
print('Рост комбинаций | одиночных:', len(ds), '| пар:', len(dp), '| троек:', len(dt))
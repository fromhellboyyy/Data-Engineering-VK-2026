import json
from collections import defaultdict, Counter
import numpy as np

with open('results/mapreduce_results.json', 'r', encoding='utf-8') as f:
    res = json.load(f)
vac = res['vacancy_data']

reg = defaultdict(lambda: {'n': 0, 'sal': [], 'sk': Counter()})
for v in vac:
    r = v['region']
    reg[r]['n'] += 1
    if v['salary'] is not None:
        reg[r]['sal'].append(v['salary'])
    for s in v['skills']:
        reg[r]['sk'][str(s).strip()] += 1

cand = [(r, d) for r, d in reg.items() if len(d['sal']) >= 1]
cand.sort(key=lambda x: x[1]['n'], reverse=True)
top3 = cand[:3]

print('Зарплаты по регионам')
print('Регион | вакансий | с ЗП | медиана ЗП')
for r, d in top3:
    med = round(float(np.median(d['sal'])))
    print(r, '|', d['n'], '|', len(d['sal']), '|', med)

print('Топ-5 навыков по регионам')
for r, d in top3:
    print('Регион:', r)
    for s, c in d['sk'].most_common(5):
        print('   ', s, ':', c)
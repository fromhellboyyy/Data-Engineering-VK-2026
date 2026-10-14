import json, itertools
from collections import defaultdict
import numpy as np

with open('results/mapreduce_results.json', 'r', encoding='utf-8') as f:
    res = json.load(f)
vac = res['vacancy_data']
paid = [v for v in vac if v['salary'] is not None]
gmed = float(np.median([v['salary'] for v in paid]))
freq = res['singles']
print('Вакансий с ЗП:', len(paid), '| глобальная медиана:', round(gmed))

base_sal = defaultdict(list)
pair_sal = defaultdict(list)
trip_sal = defaultdict(list)
for v in paid:
    sk = [str(s).strip() for s in v['skills'] if str(s).strip()]

    for s in sk:
        base_sal[s].append(v['salary'])
    for p in itertools.combinations(sk, 2):
        pair_sal[tuple(sorted(p))].append(v['salary'])
    for t in itertools.combinations(sk, 3):
        trip_sal[tuple(sorted(t))].append(v['salary'])

def impact(combo_dict, k):
    out = []
    for combo, sals in combo_dict.items():
        if len(sals) < 2:
            continue
        elems = list(combo)
        base = max(elems, key=lambda e: freq.get(e, 0))
        bl = base_sal.get(base, [])
        if len(bl) < 2:
            continue
        bm = float(np.median(bl))
        cm = float(np.median(sals))
        out.append((combo, base, round(bm), round(cm), round(cm - bm)))
    out.sort(key=lambda x: x[4], reverse=True)
    return out

def show(title, lst):
    print('---', title, '---')
    print('Вверх:')
    for c, b, bm, cm, d in lst[:3]:
        print(c, '| база:', b, '| медиана базы:', bm, '| медиана combo:', cm, '| дельта:', d)
    print('Вниз:')
    for c, b, bm, cm, d in lst[-3:]:
        print(c, '| база:', b, '| медиана базы:', bm, '| медиана combo:', cm, '| дельта:', d)

pi = impact(pair_sal, 2)
ti = impact(trip_sal, 3)
show('Пары навыков по зарплате', pi)
show('Тройки навыков по зарплате', ti)
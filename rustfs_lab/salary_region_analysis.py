import json
import numpy as np
from collections import defaultdict

with open('results/mapreduce_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

vacancies = data['vacancy_data']
paid_vacancies = [v for v in vacancies if v['salary'] is not None]

print(f"Всего вакансий: {len(vacancies)}, Из них с зарплатой: {len(paid_vacancies)}\n")

print("Анализ влияния навыков на зарплату")
skill_salaries = defaultdict(list)
for v in paid_vacancies:
    for skill in v['skills']:
        skill_salaries[skill].append(v['salary'])

global_median = np.median([v['salary'] for v in paid_vacancies])

skill_impact = []
for skill, salaries in skill_salaries.items():
    if len(salaries) >= 2:
        median_skill = np.median(salaries)
        impact = median_skill - global_median
        skill_impact.append({'skill': skill, 'count': len(salaries), 'median': median_skill, 'impact': impact})

skill_impact.sort(key=lambda x: x['impact'], reverse=True)

print(f"Глобальная медианная зарплата: {global_median:.0f} RUR\n")
print("Топ-3 навыка, повышающих зарплату:")
for item in skill_impact[:3]:
    print(f"  - {item['skill']} (встречается: {item['count']} раз, медиана: {item['median']:.0f}, влияние: +{item['impact']:.0f})")

print("\n Топ-3 навыка, понижающих зарплату:")
for item in skill_impact[-3:]:
    print(f"  - {item['skill']} (встречается: {item['count']} раз, медиана: {item['median']:.0f}, влияние: {item['impact']:.0f})")

print("\nРегиональный анализ")
region_stats = defaultdict(lambda: {'count': 0, 'salaries': [], 'skills': defaultdict(int)})

for v in vacancies:
    reg = v['region']
    region_stats[reg]['count'] += 1
    if v['salary']:
        region_stats[reg]['salaries'].append(v['salary'])
    for skill in v['skills']:
        region_stats[reg]['skills'][skill] += 1

top_regions = sorted(region_stats.items(), key=lambda x: x[1]['count'], reverse=True)[:3]

print(f"{'Регион':<25} | {'Вакансий':<8} | {'Медиана ЗП':<12} | {'Топ навык'}")
print("-" * 75)
for reg, stats in top_regions:
    median = np.median(stats['salaries']) if stats['salaries'] else 0
    top_skill = max(stats['skills'].items(), key=lambda x: x[1])[0] if stats['skills'] else 'Нет'
    print(f"{reg:<25} | {stats['count']:<8} | {median:>8.0f} RUR | {top_skill}")
import boto3
import json
import time
import tracemalloc
import itertools
import os
from collections import defaultdict

s3 = boto3.client('s3', endpoint_url='http://localhost:9000',
                  aws_access_key_id='admin', aws_secret_access_key='password123')
BUCKET = 'vacancies-dataset'

with open('csharp_files_list.txt', 'r', encoding='utf-8') as f:
    TARGET_FILES = [line.strip() for line in f if line.strip()]

CHUNK_SIZE = 10

def get_median_salary(salary):
    if not salary or not isinstance(salary, dict):
        return None
    s_from = int(salary.get('from') or 0)
    s_to = int(salary.get('to') or 0)
    return (s_from + s_to) / 2 if s_to else s_from

def run_mapreduce():
    tracemalloc.start()
    start_time = time.time()

    skill_counts = defaultdict(int)
    pair_counts = defaultdict(int)
    triple_counts = defaultdict(int)
    vacancy_data = []

    for i in range(0, len(TARGET_FILES), CHUNK_SIZE):
        chunk = TARGET_FILES[i:i + CHUNK_SIZE]
        for filename in chunk:
            try:
                response = s3.get_object(Bucket=BUCKET, Key=filename)
                data = json.loads(response['Body'].read().decode('utf-8'))

                skills = data.get('key_skills') or []
                skills = [str(s).strip() for s in skills if str(s).strip()]

                salary = get_median_salary(data.get('salary'))
                region = data.get('area', {}).get('name') if data.get('area') else 'Не указан'

                vacancy_data.append({'id': filename, 'skills': skills, 'salary': salary, 'region': region})

                for skill in skills:
                    skill_counts[skill] += 1

                for pair in itertools.combinations(skills, 2):
                    pair_counts[tuple(sorted(pair))] += 1
                for triple in itertools.combinations(skills, 3):
                    triple_counts[tuple(sorted(triple))] += 1
            except Exception as e:
                pass

    exec_time = time.time() - start_time
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        'singles': dict(sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)),
        'pairs': {f"{p[0]} + {p[1]}": c for p, c in sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)},
        'triples': {f"{t[0]} + {t[1]} + {t[2]}": c for t, c in sorted(triple_counts.items(), key=lambda x: x[1], reverse=True)},
        'vacancy_data': vacancy_data,
        'metrics': {'time_sec': exec_time, 'peak_memory_mb': peak / 1024 / 1024}
    }

print("Запуск MapReduce")
metrics = []
final_results = None

for attempt in range(3):
    print(f"Попытка {attempt + 1}:")
    final_results = run_mapreduce()
    metrics.append(final_results['metrics'])

    t = final_results['metrics']['time_sec']
    m = final_results['metrics']['peak_memory_mb']
    print(f" Время: {t:.4f} сек, Память: {m:.2f} MB")

avg_time = sum(m['time_sec'] for m in metrics) / 3
avg_mem = sum(m['peak_memory_mb'] for m in metrics) / 3
final_results['metrics'] = {'avg_time_sec': avg_time, 'avg_peak_memory_mb': avg_mem}

os.makedirs('results', exist_ok=True)
with open('results/mapreduce_results.json', 'w', encoding='utf-8') as f:
    json.dump(final_results, f, ensure_ascii=False, indent=2)
print("Результаты сохранены в results/mapreduce_results.json")

s3.put_object(Bucket=BUCKET, Key='results/mapreduce_skills.json',
              Body=json.dumps(final_results, ensure_ascii=False, indent=2).encode('utf-8'))
print("Результаты загружены в S3 (ключ: results/mapreduce_skills.json)")
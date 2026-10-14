from collections import defaultdict

import boto3

s3 = boto3.client('s3', endpoint_url='http://localhost:9000',
                  aws_access_key_id='admin', aws_secret_access_key='password123')
BUCKET = 'vacancies-dataset'

chunk = ['__NO_SUCH_KEY__.json', '77732348.json', '80044734.json']

skill_counts = defaultdict(int)
skipped = 0
processed = 0
for fn in chunk:
    try:
        resp = s3.get_object(Bucket=BUCKET, Key=fn)
        import json
        data = json.loads(resp['Body'].read().decode('utf-8'))
        skills = [str(s).strip() for s in (data.get('key_skills') or []) if str(s).strip()]
        for s in skills:
            skill_counts[s] += 1
        processed += 1
    except Exception as e:
        skipped += 1
        print('Map: пропущен недоступный объект', fn, '|', str(e)[:80])

print('Обработано маппером:', processed, '| пропущено после отказа:', skipped)
print('Редьюсер продолжил и насчитал навыков:', sum(skill_counts.values()))
print('Вывод: отказ маппера по одному объекту не обрушивает чанк и не теряет остальные данные')
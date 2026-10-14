import boto3, json, time

s3 = boto3.client('s3', endpoint_url='http://localhost:9000',
                  aws_access_key_id='admin', aws_secret_access_key='password123')
SRC = 'vacancies-dataset'
DST = 'hh-lake'

for b in [SRC, DST]:
    try:
        s3.head_bucket(Bucket=b)
        print('Бакет ок:', b)
    except Exception as e:
        print('Бакет не найден:', b, '|', e)
        raise SystemExit(1)

with open('csharp_files_list.txt', 'r', encoding='utf-8') as f:
    files = [ln.strip() for ln in f if ln.strip()]

copied = 0
for i, fn in enumerate(files):
    for attempt in range(3):
        try:
            s3.copy_object(Bucket=DST, Key=fn,
                           CopySource={'Bucket': SRC, 'Key': fn})
            copied += 1
            break
        except Exception as e:
            if 'SlowDown' in str(e):
                time.sleep(1)
            else:
                print('copy fail', fn, e)
                break
    if (i + 1) % 10 == 0:
        print(' скопировано', i + 1, 'из', len(files))

print('Файлов варианта в hh-lake:', copied)

with open('results/mapreduce_results.json', 'r', encoding='utf-8') as f:
    res = json.load(f)

for level, key in [('single', 'singles'), ('pairs', 'pairs'), ('triples', 'triples')]:
    body = json.dumps(res[key], ensure_ascii=False, indent=2).encode('utf-8')
    obj = 'skills_' + level + '.json'
    for attempt in range(3):
        try:
            s3.put_object(Bucket=DST, Key=obj, Body=body)
            print('Загружен hh-lake/', obj, '| записей:', len(res[key]))
            break
        except Exception as e:
            if 'SlowDown' in str(e):
                time.sleep(1)
            else:
                print('put fail', obj, e)
                break
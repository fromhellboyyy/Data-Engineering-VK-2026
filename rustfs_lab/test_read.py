import boto3
import sys

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='admin',
    aws_secret_access_key='password123'
)

bucket_name = 'vacancies-dataset'

try:
    response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=5)

    if 'Contents' in response:
        print(f"Бакет доступен, найдено объектов: {response['KeyCount']}")

        first_file = response['Contents'][0]['Key']

        s3.download_file(bucket_name, first_file, f'test_{first_file}')
        print(f"Файл {first_file} успешно скачан")

        import os
        os.remove(f'test_{first_file}')
    else:
        print("Бакет пуст или недоступен")

except Exception as e:
    print(f"Ошибка: {e}")
    sys.exit(1)
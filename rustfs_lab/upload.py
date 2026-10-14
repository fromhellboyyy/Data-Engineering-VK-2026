import boto3
import os


s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='admin',
    aws_secret_access_key='password123'
)

bucket_name = 'vacancies-dataset'

try:
    s3.create_bucket(Bucket=bucket_name)
    print(f"Бакет '{bucket_name}' создан")
except Exception as e:
    print(f"Бакет уже существует или ошибка: {e}")

folder_path = './json_files'
count = 0

if not os.path.exists(folder_path):
    print(f"Папка {folder_path} не найдена")
else:
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'rb') as f:
                s3.put_object(Bucket=bucket_name, Key=filename, Body=f.read())
            count += 1
            if count % 100 == 0:
                print(f"Загружено {count} файлов")
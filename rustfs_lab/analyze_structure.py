import json
import os

folder_path = './json_files'

print("Посик вакансий C# / .NET\n")

csharp_vacancies = []
keywords = ['c#', '.net', 'c sharp', 'asp.net', 'entity framework', 'wpf', 'xamarin', 'maui']

for filename in os.listdir(folder_path):
    if filename.endswith('.json'):
        with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)

                name = str(data.get('name', '')).lower()
                description = str(data.get('description', '')).lower()

                raw_skills = data.get('key_skills', [])
                if isinstance(raw_skills, list):
                    skills_text = ' '.join([str(s).lower() for s in raw_skills])
                else:
                    skills_text = ""

                is_match = any(kw in name or kw in description or kw in skills_text for kw in keywords)

                if is_match:
                    csharp_vacancies.append({
                        'filename': filename,
                        'name': data.get('name'),
                        'skills': raw_skills,
                        'salary': data.get('salary'),
                        'area': data.get('area', {}).get('name') if data.get('area') else 'Не указан'
                    })

            except Exception as e:
                continue

print(f"Найдено вакансий по варианту 'C# и .NET': {len(csharp_vacancies)}\n")

for i, vac in enumerate(csharp_vacancies[:3]):
    print(f"Вакансия {i+1}: {vac['name']}")
    print(f"  Навыки: {vac['skills']}")

    sal = vac['salary']
    if sal and isinstance(sal, dict):
        salary_from = int(sal.get('from', 0) or 0)
        salary_to = int(sal.get('to', 0) or 0)
        median_sal = (salary_from + salary_to) / 2 if salary_to else salary_from
        print(f" Зарплата (медиана): {median_sal} {sal.get('currency', 'RUR')}")
    else:
        print(" Зарплата: Не указана")

    print(f" Регион: {vac['area']}\n")

with open('csharp_files_list.txt', 'w', encoding='utf-8') as f:
    for vac in csharp_vacancies:
        f.write(vac['filename'] + '\n')

print("Список файлов сохранен в csharp_files_list.txt")
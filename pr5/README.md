# Практична робота 5

## Запуск
Потрібен Python 3.11 або 3.12. Команди виконуються з папки `pr5`:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.venv/Scripts/python.exe ingest.py
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8005
```

Відкрийте http://127.0.0.1:8005. На Linux/macOS: `python3 -m venv .venv`, далі `.venv/bin/python` замість `.venv\Scripts\python.exe`.


Перед веб-сервером збудуйте індекс. Після зміни документів, моделі або поділу повторіть ingest.py. Індекс не входить у Git. Веб-сервер без індексу запускається з підказкою. Семантичний час включає кодування запиту; перший запит також завантажує модель.

## Перевірки
З кореня репозиторію: `python -m unittest discover -s tests -v` (легкі залежності: requirements-test.txt).
Порівняння: `python compare/run.py`; деталі в compare/README.md.


## Архітектура
documents.py читає метадані й ділить текст за розділами та абзацами; embeddings.py кодує E5 з префіксами query/passage; index.py зберігає NumPy+JSON і ранжує за косинусом; keyword.py реалізує BM25. search_service.py застосовує політику доступу і перевіряє підпис індексу. Фільтри застосовуються до вибору top-k. Статус за замовчуванням чинний; архів можна обрати явно. Внутрішні матеріали клієнту недоступні.

# Практична робота 4

## Запуск
Потрібен Python 3.11 або 3.12. Команди виконуються з папки `pr4`:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8004
```

Відкрийте http://127.0.0.1:8004. На Linux/macOS: `python3 -m venv .venv`, далі `.venv/bin/python` замість `.venv\Scripts\python.exe`.
Для ПР3/ПР4 перед запуском заповніть LLM_API_KEY і LLM_MODEL у .env. Модель обирається зі списку доступних вашому акаунту. Зміна правил context.md застосовується до наступного запиту. Не публікуйте ключ.



## Перевірки
З кореня репозиторію: `python -m unittest discover -s tests -v` (легкі залежності: requirements-test.txt).
Порівняння: `python compare/run.py`; деталі в compare/README.md.


## Архітектура
schema.py визначає суворий контракт; llm.py перевіряє відповідь і обрізає найстаріші пари історії за бюджетом. Бюджет приблизний: символи/2 + службовий запас; резерв відповіді задає LLM_MAX_TOKENS окремо. Історія зберігається в пам’яті сервера до години; запускати одним worker. Перезапуск скидає розмови; для production потрібне зовнішнє сховище. Демосервер послідовно обробляє діалоги.

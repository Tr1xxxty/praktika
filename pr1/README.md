# Практична робота 1

## Запуск
Потрібен Python 3.11 або 3.12. Команди виконуються з папки `pr1`:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Відкрийте http://127.0.0.1:8001. На Linux/macOS: `python3 -m venv .venv`, далі `.venv/bin/python` замість `.venv\Scripts\python.exe`.




## Перевірки
З кореня репозиторію: `python -m unittest discover -s tests -v` (легкі залежності: requirements-test.txt).



## Архітектура
weather.py відповідає за HTTP і перевірку JSON; main.py перетворює помилки на HTTP-статуси. Геокодування обирає перший збіг: для міст з однаковими назвами можливе неоднозначне визначення.

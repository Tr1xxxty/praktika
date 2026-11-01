# Практична робота 2

## Запуск
Потрібен Python 3.11 або 3.12. Команди виконуються з папки `pr2`:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

Відкрийте http://127.0.0.1:8002. На Linux/macOS: `python3 -m venv .venv`, далі `.venv/bin/python` замість `.venv\Scripts\python.exe`.

Перше використання завантажує YOLO. CPU достатньо. Поріг задається на сторінці. Час не включає завантаження ваг і декодування зображення.


## Перевірки
З кореня репозиторію: `python -m unittest discover -s tests -v` (легкі залежності: requirements-test.txt).

Оцінювання: `python eval/prepare.py`, потім `python eval/run.py`. Деталі у eval/README.md.

## Архітектура
detector.py декодує зображення, один раз завантажує модель і серіалізує результат. Блокування захищає спільну модель. Координати xyxy у пікселях після EXIF-повороту.

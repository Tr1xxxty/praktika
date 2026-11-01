# Оцінювання детектора
З папки pr2: `python eval/prepare.py`, потім `python eval/run.py`.
П'ять різних зображень із scikit-image: astronaut (person), chelsea (cat), coffee (cup, spoon, dining table), camera (person), coins (жодного цільового об'єкта COCO). Останнє зображення перевіряє хибні спрацювання.
Джерело та атрибуція зображень: https://scikit-image.org/docs/stable/api/skimage.data.html; відповідні примітки у функціях data.astronaut, data.chelsea, data.coffee, data.camera, data.coins.
Три пороги: 0.25, 0.5, 0.75. Скрипт порівнює кількість за класами, зберігає рамки та час; неправильні класи й дублі слід перевірити за зображенням, а не вважати кожен зайвий об'єкт дублем.

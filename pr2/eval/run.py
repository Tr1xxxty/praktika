import json
import sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from app.detector import detect
cases=json.loads((ROOT/'expected.json').read_text(encoding='utf-8'))
rows=[]
for threshold in [.25,.5,.75]:
    for case in cases:
        result=detect((ROOT/'images'/case['file']).read_bytes(),threshold)
        found=Counter(o['class'] for o in result['objects']);wanted=Counter(case['expected'])
        rows.append({'file':case['file'],'threshold':threshold,**result,
                     'expected':dict(wanted),'missing':dict(wanted-found),'extra':dict(found-wanted)})
(ROOT/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# Оцінювання YOLO','','Класи й кількість розмічено вручну. Missing/extra — розбіжності за класом; вони не доводять неправильний клас чи дубль без перевірки рамок.','', '| Файл | Поріг | Пропущені | Зайві | Час, с |','|---|---|---|---|---|']
for r in rows:lines.append(f"| {r['file']} | {r['threshold']} | {r['missing']} | {r['extra']} | {r['elapsed']:.3f} |")
lines += ['','Порівняйте пороги: підвищення відсікає слабкі детекції та може збільшувати пропуски. Перевірте координати рамок у results.json для відокремлення дублів від хибних класів. Час першого inference може включати прогрів моделі.']
(ROOT/'results.md').write_text('\n'.join(lines),encoding='utf-8')
print('Результати: eval/results.json, eval/results.md')

"""Створити відтворюваний набір з відкритих зображень scikit-image."""
import json
from pathlib import Path
from PIL import Image
from skimage import data
ROOT=Path(__file__).resolve().parent
(ROOT/'images').mkdir(exist_ok=True)
# П'ять вихідних сюжетів; у наборі є позитивні та негативні приклади.
cases=[('astronaut',data.astronaut,{'person':1}),('chelsea',data.chelsea,{'cat':1}),
       ('coffee',data.coffee,{'cup':1,'spoon':1,'dining table':1}),('camera',data.camera,{'person':1}),
       ('coins',data.coins,{})]
expected=[]
for name,loader,classes in cases:
    path=ROOT/'images'/f'{name}.png'
    Image.fromarray(loader()).save(path)
    expected.append({'file':path.name,'expected':classes})
(ROOT/'expected.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2),encoding='utf-8')
print('Створено 5 зображень і expected.json')

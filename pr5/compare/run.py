import json
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app import documents, embeddings, index, keyword
cases=json.loads((ROOT/'compare/queries.json').read_text(encoding='utf-8'))['запити']
rows=[]
original=documents.CHUNK_SIZE
for size in [original,original+300]:
    documents.CHUNK_SIZE=size
    chunks=documents.load_chunks()
    idx=index.build(chunks,embeddings.embed_passages([c.text for c in chunks]),embeddings.MODEL_NAME)
    words=keyword.build(chunks)
    for case in cases:
        filters={'status':'чинний','audience':'клієнти',**case.get('фільтр',{})}
        expected=case['очікуваний_документ']
        # Внутрішній документ має бути недоступним: окремий негативний тест.
        accessible=bool(expected) and case['вид']!='внутрішній документ'
        for method in ['semantic','keyword']:
            started=time.perf_counter()
            hits=(index.search(idx,embeddings.embed_query(case['запит']),50,filters,None) if method=='semantic'
                  else keyword.search(words,case['запит'],50,filters))
            elapsed=time.perf_counter()-started
            rank=next((i+1 for i,h in enumerate(hits) if h.chunk.source==expected),None)
            rows.append({'chunk_size':size,'method':method,'query':case['запит'],'expected':expected,
                         'accessible':accessible,'rank':rank,'top_score':hits[0].score if hits else None,
                         'higher_results':[{'source':h.chunk.source,'score':h.score} for h in hits[:(rank-1 if rank else 3)]],
                         'elapsed':elapsed,'sources':[h.chunk.source for h in hits[:3]]})
    (ROOT/'compare/results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# Порівняння пошуку','','Час семантичного пошуку включає кодування запиту. Модель прогріта під час індексування. Внутрішні й відсутні відповіді виключено з hit@k та перевіряються окремо.','', '| Розмір | Метод | hit@1 | hit@3 | Середній час, с |','|---|---|---|---|---|']
for size in [original,original+300]:
    for method in ['semantic','keyword']:
        subset=[r for r in rows if r['chunk_size']==size and r['method']==method and r['accessible']]
        h1=sum(r['rank']==1 for r in subset)/len(subset)
        h3=sum(r['rank'] is not None and r['rank']<=3 for r in subset)/len(subset)
        lines.append(f"| {size} | {method} | {h1:.3f} | {h3:.3f} | {sum(r['elapsed'] for r in subset)/len(subset):.4f} |")
# Калібрування лише на базовому розмірі, без прихованої зміни конфігурації.
base=[r for r in rows if r['chunk_size']==original and r['method']=='semantic']
positive=[r['top_score'] for r in base if r['accessible'] and r['top_score'] is not None]
negative=[r['top_score'] for r in base if not r['expected'] and r['top_score'] is not None]
if positive and negative:
    threshold=(min(positive)+max(negative))/2 if min(positive)>max(negative) else max(negative)+0.001
    lost=sum(v<threshold for v in positive)
    lines += ['',f'Пробний поріг SIMILARITY_THRESHOLD={threshold:.4f}. На цьому наборі відсікає {lost}/{len(positive)} запитів з відповіддю. Це калібрування на малому наборі, а не незалежна оцінка. Перенесіть значення у .env лише після перегляду помилок.']
lines += ['','Змінено лише розмір фрагмента; модель, префікси й фільтри однакові. Деталі помилок і результати вище очікуваного документа — у results.json.']
(ROOT/'compare/results.md').write_text('\n'.join(lines),encoding='utf-8')
print('Готово: compare/results.json, compare/results.md')

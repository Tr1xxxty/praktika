import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app import llm
cases = json.loads((ROOT/'compare/requests.json').read_text(encoding='utf-8'))
context = (ROOT/'context.md').read_text(encoding='utf-8')
rows = []
configs = ['vague', 'structured', 'context']
for config in configs:
    sequences = [[c['текст']] for c in cases['звернення']]
    sequences += [d['репліки'] for d in cases.get('діалоги',[])]
    for case_id, sequence in enumerate(sequences):
        history = []
        for turn, text in enumerate(sequence):
            row = {'config':config,'case':case_id,'turn':turn,'question':text}
            try:
                result = llm.ask(text,history,context,mode=config,enforce=False)
                row.update(result)
                reply = result.get('answer') or (result.get('result') or {}).get('reply') or result.get('raw','')
                history += [{'role':'user','content':text},{'role':'assistant','content':reply}]
                row['review'] = {'factual_error':None,'correct_topic':None,'remembers_order':None,'error_type':None}
            except llm.LLMError as exc: row.update(error=str(exc),status=exc.status)
            rows.append(row)
            (ROOT/'compare/results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
summary = ['# Результати порівняння','', 'Фактичну правильність перевірте вручну за context.md; поля review=null означають, що перевірку ще не виконано.','']
for config in configs:
    subset=[r for r in rows if r['config']==config]
    good=[r for r in subset if 'elapsed' in r]
    summary.append(f"- Конфігурація {config}: {len(good)} відповідей, {len(subset)-len(good)} помилок; середній час {sum(r['elapsed'] for r in good)/max(1,len(good)):.3f} с.")
summary += ['','Повні відповіді, токени й помилки: results.json. Порівняйте довжину, факти, збереження номера замовлення та класифікуйте синтаксичні, семантичні, фактичні, контекстні й поведінкові помилки.']
(ROOT/'compare/results.md').write_text('\n'.join(summary),encoding='utf-8')
print('Результати записано в compare/results.json і results.md')

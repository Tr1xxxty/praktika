import re
from dataclasses import dataclass
import numpy as np
from rank_bm25 import BM25Okapi
from .index import Hit, eligible, DEFAULT_TOP_K
@dataclass
class KeywordIndex:
    chunks: list
    model: object

def tokenize(text):
    return re.findall(r"[\w]+(?:[-'’ʼ][\w]+)*",text.lower().replace('’',"'").replace('ʼ',"'"))
def build(chunks):
    if not chunks: raise ValueError('Немає фрагментів')
    return KeywordIndex(chunks,BM25Okapi([tokenize(c.text) for c in chunks]))
def search(index, query, top_k=DEFAULT_TOP_K, filters=None):
    if not 1 <= top_k <= 50: raise ValueError('Некоректний top_k')
    tokens = tokenize(query)
    if not tokens: return []
    scores = index.model.get_scores(tokens)
    ids = eligible(index.chunks,filters)
    ids.sort(key=lambda i:float(scores[i]),reverse=True)
    return [Hit(index.chunks[i],float(scores[i])) for i in ids if scores[i]>0][:top_k]

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
import numpy as np
from dotenv import load_dotenv
from .documents import Chunk
load_dotenv(Path(__file__).resolve().parent.parent/'.env')
INDEX_DIR = Path(__file__).resolve().parent.parent/'index'
DEFAULT_TOP_K = int(os.getenv('SEARCH_TOP_K','5'))
SIMILARITY_THRESHOLD = float(os.environ['SIMILARITY_THRESHOLD']) if os.getenv('SIMILARITY_THRESHOLD','').strip() else None
FIELDS = {'category','product','audience','status'}
@dataclass
class Hit:
    chunk: Chunk
    score: float
@dataclass
class SearchIndex:
    chunks: list[Chunk]
    vectors: np.ndarray
    model_name: str
    extra: dict = field(default_factory=dict)
    def __len__(self): return len(self.chunks)
def normalize(vectors):
    v = np.asarray(vectors,dtype=np.float32)
    if not np.isfinite(v).all(): raise ValueError('Некоректні вектори')
    norms = np.linalg.norm(v,axis=-1,keepdims=True)
    if np.any(norms == 0): raise ValueError('Нульовий вектор')
    return v/norms
def build(chunks, vectors, model_name):
    v = np.asarray(vectors)
    if v.ndim != 2 or len(v) != len(chunks) or not len(chunks): raise ValueError('Розміри індексу не збігаються')
    return SearchIndex(chunks,normalize(v),model_name)
def save(index, path=INDEX_DIR):
    path = Path(path);path.mkdir(parents=True,exist_ok=True)
    np.save(path/'vectors.npy',index.vectors,allow_pickle=False)
    payload = {'version':1,'model_name':index.model_name,'extra':index.extra,
               'chunks':[asdict(c) for c in index.chunks]}
    (path/'metadata.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
def load(path=INDEX_DIR):
    path = Path(path)
    try:
        data = json.loads((path/'metadata.json').read_text(encoding='utf-8'))
        if data['version'] != 1: raise ValueError('Невідома версія індексу')
        result = build([Chunk(**c) for c in data['chunks']],np.load(path/'vectors.npy',allow_pickle=False),data['model_name'])
        result.extra = data['extra']
        return result
    except FileNotFoundError as exc: raise ValueError('Індекс не збудовано: python ingest.py') from exc

def eligible(chunks, filters=None):
    filters = filters or {}
    if set(filters)-FIELDS: raise ValueError('Невідоме поле фільтра')
    if any(not isinstance(v,str) for v in filters.values()): raise ValueError('Значення фільтра має бути рядком')
    return [i for i,c in enumerate(chunks) if all(c.metadata.get(k)==v for k,v in filters.items())]
def search(index, query_vector, top_k=DEFAULT_TOP_K, filters=None, threshold=SIMILARITY_THRESHOLD):
    if not 1 <= top_k <= 50: raise ValueError('top_k має бути від 1 до 50')
    q = np.asarray(query_vector)
    if q.shape != (index.vectors.shape[1],): raise ValueError('Розмірність моделі не збігається')
    ids = eligible(index.chunks,filters)
    scores = index.vectors @ normalize(q)
    ranked = sorted(ids,key=lambda i:float(scores[i]),reverse=True)
    return [Hit(index.chunks[i],float(scores[i])) for i in ranked if threshold is None or scores[i]>=threshold][:top_k]

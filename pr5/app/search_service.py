import hashlib
import time
from pathlib import Path
from . import embeddings, index, keyword, documents

def signature():
    digest = hashlib.sha256()
    for p in sorted(documents.DOCS_DIR.glob('*.md')):
        if p.name.lower() != 'readme.md': digest.update(p.name.encode()); digest.update(p.read_bytes())
    return {'documents_sha256':digest.hexdigest(), 'chunk_size':documents.CHUNK_SIZE,
            'chunk_overlap':documents.CHUNK_OVERLAP,'split_version':1,
            'query_prefix':embeddings.QUERY_PREFIX,'passage_prefix':embeddings.PASSAGE_PREFIX}

class SearchService:
    def __init__(self):
        self.idx = None
        self.hint = 'Виконайте python ingest.py'
        try:
            idx = index.load()
            if idx.model_name != embeddings.MODEL_NAME or idx.extra != signature():
                raise ValueError('Документи або налаштування змінені: виконайте python ingest.py')
            self.words = keyword.build(idx.chunks)
            self.idx = idx
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.hint = str(exc)
    def status(self):
        if self.idx is None: return {'ready':False,'hint':self.hint}
        return {'ready':True,'chunks':len(self.idx),'documents':len({c.source for c in self.idx.chunks}),'model':self.idx.model_name}
    def search(self, query, mode, top_k, filters, threshold):
        if self.idx is None: raise RuntimeError(self.hint)
        # Публічний інтерфейс не дозволяє відкрити внутрішні матеріали.
        if filters.get('audience','клієнти') != 'клієнти': raise PermissionError('Внутрішні документи недоступні клієнтам')
        filters = {'status':'чинний',**filters,'audience':'клієнти'}
        index.eligible(self.idx.chunks,filters)
        result = {'query':query,'semantic':None,'keyword':None,'elapsed':{}}
        for method in ('semantic','keyword'):
            if mode not in (method,'both'): continue
            started = time.perf_counter()
            if method == 'semantic':
                hits = index.search(self.idx,embeddings.embed_query(query),top_k,filters,threshold)
            else: hits = keyword.search(self.words,query,top_k,filters)
            result['elapsed'][method] = time.perf_counter()-started
            result[method] = [{'score':h.score,'text':h.chunk.text,'source':h.chunk.source,'metadata':h.chunk.metadata} for h in hits]
        return result

import os
import threading
from pathlib import Path
import numpy as np
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent/'.env')
MODEL_NAME = os.getenv('EMBEDDING_MODEL','intfloat/multilingual-e5-small')
QUERY_PREFIX = os.getenv('QUERY_PREFIX','query: ')
PASSAGE_PREFIX = os.getenv('PASSAGE_PREFIX','passage: ')
_model = None
_lock = threading.Lock()
def get_model():
    global _model
    with _lock:
        if _model is None:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(MODEL_NAME, device='cpu')
        return _model
def encode(texts, prefix):
    model = get_model()
    inputs = [prefix+t for t in texts]
    lengths = [len(model.tokenizer.encode(t, add_special_tokens=True)) for t in inputs]
    if any(n > model.max_seq_length for n in lengths):
        raise ValueError('Текст перевищує ліміт моделі: зменште CHUNK_SIZE або запит')
    with _lock:
        return np.asarray(model.encode(inputs, normalize_embeddings=True, show_progress_bar=False),dtype=np.float32)
def embed_passages(texts):
    return encode(texts,PASSAGE_PREFIX)
def embed_query(text):
    return encode([text],QUERY_PREFIX)[0]

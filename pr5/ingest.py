"""Побудова індексу: python ingest.py."""

import sys
import time
from collections import Counter

from app import documents, embeddings, index


def main() -> int:
    started = time.perf_counter()
    docs = documents.load_documents()
    print(f"Документів: {len(docs)}")

    chunks = documents.load_chunks()
    per_doc = Counter(chunk.source for chunk in chunks)
    lengths = [len(chunk.text) for chunk in chunks]
    print(f"Фрагментів: {len(chunks)}")
    if chunks:
        print(f"  довжина, символів: min {min(lengths)}, "
              f"середня {sum(lengths) // len(lengths)}, max {max(lengths)}")
        for source, count in sorted(per_doc.items()):
            print(f"  {count:3d}  {source}")

    print(f"Модель: {embeddings.MODEL_NAME}")
    t_embed = time.perf_counter()
    vectors = embeddings.embed_passages([chunk.text for chunk in chunks])
    print(f"Вектори: {vectors.shape[0]} × {vectors.shape[1]} "
          f"за {time.perf_counter() - t_embed:.1f} с")

    built = index.build(chunks, vectors, embeddings.MODEL_NAME)
    from app.search_service import signature
    built.extra = signature()
    index.save(built)
    print(f"Індекс збережено у {index.INDEX_DIR} "
          f"({time.perf_counter() - started:.1f} с загалом)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

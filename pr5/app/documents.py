"""Читання Markdown, метаданих і поділ на фрагменти."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DOCS_DIR = Path(__file__).parent.parent / "docs"

# Параметри поділу — відправна точка, а не рекомендація. У чому їх
# рахувати (символи, слова, токени моделі) і як застосовувати, коли
# ділите за заголовками, — ваше рішення.
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))


@dataclass
class Chunk:
    """Фрагмент документа — одиниця індексування й пошуку.

    `text` — те, що перетворюється на вектор і показується в результатах.
    `source` — імʼя файлу, з якого взято фрагмент.
    `metadata` — поля з блоку метаданих файлу (title, category, product,
    audience, updated, status) плюс те, що ви вирішите додати самі:
    заголовок розділу, порядковий номер фрагмента, позицію в документі.
    Фільтри пошуку працюють саме з цим словником.
    """

    text: str
    source: str
    metadata: dict = field(default_factory=dict)


def parse_front_matter(raw: str) -> tuple[dict, str]:
    """Відокремити блок метаданих від тексту документа.

    Блок — рядки `ключ: значення` між двома рядками `---` на початку
    файлу. Повертає словник метаданих і решту тексту. Порожні значення
    (`product:` без нічого) стають порожнім рядком. Якщо блоку немає —
    порожній словник і текст як є.
    """
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, raw
    metadata: dict = {}
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            body = "\n".join(lines[i + 1:]).lstrip("\n")
            return metadata, body
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip()] = value.strip()
    return {}, raw


def load_documents(docs_dir: Path = DOCS_DIR) -> list[tuple[str, dict, str]]:
    """Прочитати всі документи колекції.

    Повертає список трійок (імʼя файлу, метадані, текст) для кожного
    `*.md` у папці, крім `README.md` — він описує колекцію, а не є її
    частиною. Порядок — за іменем файлу, щоб індекс будувався однаково
    від запуску до запуску.
    """
    documents = []
    for path in sorted(docs_dir.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        metadata, body = parse_front_matter(path.read_text(encoding="utf-8"))
        documents.append((path.name, metadata, body))
    return documents


def split(text: str, source: str, metadata: dict) -> list[Chunk]:
    import re
    if CHUNK_SIZE < 100 or not 0 <= CHUNK_OVERLAP < CHUNK_SIZE:
        raise ValueError("Потрібно CHUNK_SIZE >= 100 та 0 <= CHUNK_OVERLAP < CHUNK_SIZE")
    chunks = []
    heading = metadata.get('title', source)
    buffer = ''
    def emit(body):
        if body.strip():
            chunks.append(Chunk(heading + "\n" + body.strip(), source,
                                {**metadata, 'section':heading, 'chunk_id':len(chunks)}))
    # Межі розділів зберігаються; довгі блоки діляться по рядках/словах.
    for block in re.split(r"\n\s*\n", text):
        if not block.strip(): continue
        if block.startswith('#'):
            emit(buffer); buffer = ''
            lines = block.splitlines()
            heading = metadata.get('title',source) + ' — ' + lines[0].lstrip('# ')
            block = '\n'.join(lines[1:])
        if not block: continue
        if len(buffer) + len(block) > CHUNK_SIZE:
            emit(buffer)
            buffer = ''
        while len(block) > CHUNK_SIZE:
            cut = block.rfind('\n', 0, CHUNK_SIZE)
            if cut < CHUNK_SIZE//2: cut = block.rfind(' ',0,CHUNK_SIZE)
            if cut <= CHUNK_OVERLAP: cut = CHUNK_SIZE
            emit(block[:cut])
            next_start = cut - CHUNK_OVERLAP
            if next_start:
                boundary = block.find(' ', next_start, cut)
                if boundary >= 0: next_start = boundary+1
            block = block[next_start:]
        buffer = (buffer+'\n\n'+block).strip()
    emit(buffer)
    return chunks


def load_chunks(docs_dir: Path = DOCS_DIR) -> list[Chunk]:
    """Прочитати колекцію й повернути всі її фрагменти."""
    chunks: list[Chunk] = []
    for source, metadata, body in load_documents(docs_dir):
        chunks.extend(split(body, source, metadata))
    return chunks

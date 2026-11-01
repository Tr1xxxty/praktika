from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from .search_service import SearchService
from .index import DEFAULT_TOP_K, SIMILARITY_THRESHOLD
@asynccontextmanager
async def lifespan(app):
    app.state.search = SearchService()
    yield
app = FastAPI(title='Пошук — ПР5',lifespan=lifespan)
class SearchRequest(BaseModel):
    query: str = Field(min_length=1,max_length=2000)
    mode: Literal['semantic','keyword','both'] = 'both'
    top_k: int = Field(default=DEFAULT_TOP_K,ge=1,le=50)
    filters: dict[str,str] = Field(default_factory=dict)
    threshold: float | None = Field(default=SIMILARITY_THRESHOLD,ge=-1,le=1)
@app.get('/',response_class=HTMLResponse)
def page(): return (Path(__file__).parent/'templates/index.html').read_text(encoding='utf-8')
@app.get('/api/status')
def status(): return app.state.search.status()
@app.post('/api/search')
def search(payload: SearchRequest):
    if not payload.query.strip(): raise HTTPException(422,'Введіть запит')
    try:
        return app.state.search.search(payload.query.strip(),payload.mode,payload.top_k,payload.filters,payload.threshold if payload.threshold is not None else SIMILARITY_THRESHOLD)
    except PermissionError as exc: raise HTTPException(403,str(exc)) from exc
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(503,str(exc)) from exc
    except Exception as exc: raise HTTPException(503,'Не вдалося завантажити модель або виконати пошук') from exc

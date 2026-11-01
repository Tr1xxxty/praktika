from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
app = FastAPI(title="ПР3")
ROOT = Path(__file__).resolve().parent.parent
@app.get("/", response_class=HTMLResponse)
def page():
    return (ROOT / "app/templates/index.html").read_text(encoding="utf-8")

from pydantic import BaseModel, Field
from . import llm
class Question(BaseModel):
    question: str = Field(max_length=8000)
@app.post("/api/ask")
def ask(payload: Question):
    try:
        return llm.ask(payload.question, (ROOT / 'context.md').read_text(encoding='utf-8'))
    except llm.LLMError as exc:
        raise HTTPException(exc.status, str(exc)) from exc
    except OSError as exc:
        raise HTTPException(503, "Не вдалося прочитати context.md") from exc

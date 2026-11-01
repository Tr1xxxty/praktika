from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
app = FastAPI(title="ПР4")
ROOT = Path(__file__).resolve().parent.parent
@app.get("/", response_class=HTMLResponse)
def page():
    return (ROOT / "app/templates/index.html").read_text(encoding="utf-8")

import secrets
import threading
import time
from fastapi import Request, Response
from pydantic import BaseModel, ConfigDict, Field
from . import llm
class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(max_length=8000)
_sessions = {}
_lock = threading.Lock()
@app.post("/api/chat")
def chat(payload: ChatRequest, request: Request, response: Response):
    # Однопроцесний навчальний сервер: історія не надходить від клієнта.
    with _lock:
        now = time.time()
        for key in list(_sessions):
            if now-_sessions[key][0] > 3600: del _sessions[key]
        sid = request.cookies.get('conversation')
        if sid not in _sessions:
            if len(_sessions) >= 200: _sessions.pop(min(_sessions,key=lambda k:_sessions[k][0]))
            sid = secrets.token_urlsafe(32)
            _sessions[sid] = (now, [])
        history = _sessions[sid][1]
        try:
            result = llm.ask(payload.message, history, (ROOT/'context.md').read_text(encoding='utf-8'))
        except llm.LLMError as exc: raise HTTPException(exc.status,str(exc)) from exc
        except OSError as exc: raise HTTPException(503,'Не вдалося прочитати context.md') from exc
        history = history + [{'role':'user','content':payload.message}, {'role':'assistant','content':result['result']['reply']}]
        _sessions[sid] = (now, history[-40:])
    response.set_cookie('conversation', sid, httponly=True, samesite='strict', max_age=3600)
    return result
@app.post('/api/reset')
def reset(request: Request, response: Response):
    with _lock: _sessions.pop(request.cookies.get('conversation'),None)
    response.delete_cookie('conversation')
    return {'ok':True}

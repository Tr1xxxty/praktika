from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
app = FastAPI(title="ПР2")
ROOT = Path(__file__).resolve().parent.parent
@app.get("/", response_class=HTMLResponse)
def page():
    return (ROOT / "app/templates/index.html").read_text(encoding="utf-8")

from fastapi import File, UploadFile, Form
from starlette.concurrency import run_in_threadpool
from . import detector
@app.post("/api/detect")
async def api_detect(image: UploadFile = File(...), confidence: float = Form(detector.DEFAULT_CONFIDENCE)):
    content = await image.read(detector.MAX_BYTES + 1)
    await image.close()
    try:
        return await run_in_threadpool(detector.detect, content, confidence)
    except detector.DetectionError as exc:
        raise HTTPException(exc.status, str(exc)) from exc

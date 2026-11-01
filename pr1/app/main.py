from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
app = FastAPI(title="ПР1")
ROOT = Path(__file__).resolve().parent.parent
@app.get("/", response_class=HTMLResponse)
def page():
    return (ROOT / "app/templates/index.html").read_text(encoding="utf-8")

from . import weather
@app.get("/api/weather")
def api_weather(city: str = ""):
    try:
        return weather.get_current_weather(city)
    except weather.WeatherError as exc:
        raise HTTPException(exc.status, str(exc)) from exc

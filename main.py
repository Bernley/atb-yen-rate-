import time
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from parser import get_jpy_buy_rate

app = FastAPI()
app.mount("/static", StaticFiles(directory="templates"), name="static")
templates = Jinja2Templates(directory="templates")

CACHE_TTL = 3600

_cache: dict = {"rate": None, "updated_at": 0.0, "error": False}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    now = time.time()
    if _cache["rate"] is None or now - _cache["updated_at"] > CACHE_TTL:
        try:
            _cache["rate"] = get_jpy_buy_rate()
            _cache["updated_at"] = now
            _cache["error"] = False
        except Exception:
            _cache["error"] = True

    updated = (
        datetime.fromtimestamp(_cache["updated_at"]).strftime("%d %B %Y, %H:%M")
        if _cache["updated_at"]
        else None
    )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "rate": _cache["rate"],
            "updated": updated,
            "error": _cache["error"],
        },
    )

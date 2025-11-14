from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Any, Dict, Optional
import os
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.user_configs import user_config

# try:
#     # from config import user_config as _uc_mod
#     from config.user_configs import user_config
# except Exception:
#     _uc_mod = None

def _load_user_context() -> Dict[str, Optional[Any]]:

    # fallback = {
    #     "id": None,
    #     "name": "Guest",
    #     "email": None,
    #     "farm_id": None,
    #     "location": None,
    #     "sido_map_full": None,
    # }

    # if not _uc_mod:
    #     return fallback

    # uc = getattr(_uc_mod, "user_config", None)
    # if not uc:
    #     return fallback

    ## Safely fetch attributes if present
    return {
        "id": user_config.ID, #getattr(uc, "ID", None),
        "name": user_config.NAME, #getattr(uc, "NAME", None) or getattr(uc, "name", None) or "Guest",
        "email": user_config.EMAIL, #getattr(uc, "EMAIL", None),
        "farm_id": user_config.FARM_ID, #getattr(uc, "FARM_ID", None),
        "location": user_config.LOCATION, #getattr(uc, "LOCATION", None),
        "location_name": user_config.LOCATION_NAME, #getattr(uc, "sido_map_full", None),
    }


app = FastAPI(
    title="AI Chat Assistant",
    description="Simple FastAPI app serving templates for AI chat and diaries.",
    version="1.0.0",
)

# 정적 파일이 있다면 사용 (없으면 주석 처리해도 됨)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# 템플릿 디렉토리 설정
templates = Jinja2Templates(directory="test_app/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):

    u = _load_user_context()
    # api_base_url = getattr(request.app.state, "api_base_url", "")

    context = {
        "request": request,
        "current_user_name": u.get("name"),
        "current_user_email": u.get("email"),
        "current_user_id": u.get("id"),
        "current_user_farm_id": u.get("farm_id"),
        "current_user_location": u.get("location"),
        "current_user_location_name": u.get("location_name"),
        # "api_base_url": api_base_url,
    }
    print('context:', context)
    return templates.TemplateResponse("index.html", context)


@app.get("/info", response_class=HTMLResponse)
async def info(request: Request):
    return templates.TemplateResponse("info.html", {"request": request})

@app.get("/settings_guide", response_class=HTMLResponse)
async def settings_guide(request: Request):
    return templates.TemplateResponse("settings_guide.html", {"request": request})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the test_app FastAPI server.")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind (default: 0.0.0.0 or $HOST)")
    parser.add_argument("--port", type=int, default=int(8001), help="Port to bind (default: 8559 or $PORT)")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn reload (useful for development).")
    # parser.add_argument("--api_host", type=str, default="127.0.0.1", help="API host (no scheme). Combined with --api-port.")
    # parser.add_argument("--api_port", type=int, default=8000, help="API port (combined with --api-host).")
    args = parser.parse_args()

    # api_base_url = f"http://{args.api_host}:{args.api_port}" # http://127.0.0.1:8668
    # print(' - api base url:', api_base_url)

    # app.state.api_base_url = api_base_url
    
    import uvicorn

    # Run uvicorn with parsed args; allows overriding port via CLI or environment variable PORT
    uvicorn.run("client_server:app", host=args.host, port=args.port, reload=args.reload)
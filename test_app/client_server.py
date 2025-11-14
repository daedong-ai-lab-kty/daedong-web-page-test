from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Any, Dict, Optional
import os
import argparse
from pathlib import Path
import sys
import importlib
import threading
import traceback

# ensure project root is on sys.path so config imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# dynamic reload fallback reference for user_configs
try:
    import config.user_configs as _uc_mod_fallback
except Exception:
    _uc_mod_fallback = None

# We will read web_config.yaml on each request using ConfigYamlLoader
try:
    from config.config_file_loader import ConfigYamlLoader
except Exception:
    ConfigYamlLoader = None

# lock to avoid concurrent reload races for user config
_user_reload_lock = threading.Lock()

def _load_user_context() -> Dict[str, Optional[Any]]:
    """
    Load current user context by reloading config.user_configs module on each call.
    This ensures that if config/user_configs.py is overwritten at runtime (e.g., via /set_main_user),
    the next request sees the updated values.
    """
    try:
        with _user_reload_lock:
            try:
                import config.user_configs as uc_mod
            except Exception:
                uc_mod = _uc_mod_fallback

            if uc_mod is None:
                return {
                    "id": None,
                    "name": None,
                    "email": None,
                    "farm_id": None,
                    "location": None,
                    "location_name": None,
                }

            # Try to reload the module to pick up file changes; if reload fails, continue with existing object
            try:
                importlib.reload(uc_mod)
            except Exception as e:
                print("[_load_user_context] config.user_configs reload failed:", e)
                traceback.print_exc()

            uc = getattr(uc_mod, "user_config", None)
            if not uc:
                return {
                    "id": None,
                    "name": None,
                    "email": None,
                    "farm_id": None,
                    "location": None,
                    "location_name": None,
                }

            try:
                return {
                    "id": getattr(uc, "ID", None),
                    "name": getattr(uc, "NAME", None),
                    "email": getattr(uc, "EMAIL", None),
                    "farm_id": getattr(uc, "FARM_ID", None),
                    "location": getattr(uc, "LOCATION", None),
                    "location_name": getattr(uc, "LOCATION_NAME", None),
                }
            except Exception as e:
                print("[_load_user_context] error reading attributes from user_config:", e)
                traceback.print_exc()
                return {
                    "id": None,
                    "name": None,
                    "email": None,
                    "farm_id": None,
                    "location": None,
                    "location_name": None,
                }
    except Exception as e:
        print("[_load_user_context] unexpected error:", e)
        traceback.print_exc()
        return {
            "id": None,
            "name": None,
            "email": None,
            "farm_id": None,
            "location": None,
            "location_name": None,
        }

def _get_web_defaults():
    """
    Read config/web_config.yaml on each call and return (base_url, endpoint).
    This avoids depending on an imported module that was loaded once at process start.
    """
    try:
        if ConfigYamlLoader is None:
            return "", ""
        loader = ConfigYamlLoader()
        cfg = loader.load_config('config/web_config.yaml') or {}
        # loader returns parsed yaml structure (dict)
        web = cfg.get('web', {}) if isinstance(cfg, dict) else {}
        base = web.get('base_server_address') or web.get('BASE_SERVER_ADDRESS') or ""
        endpoint = web.get('base_endpoint') or web.get('BASE_ENDPOINT') or ""
        print('- _get_web_defaults base:', base)
        print('- _get_web_defaults endpoint:', endpoint)
        return str(base), str(endpoint)
    except Exception as e:
        print("[_get_web_defaults] failed to load web_config.yaml:", e)
        traceback.print_exc()
        return "", ""

app = FastAPI(
    title="AI Chat Assistant",
    description="Simple FastAPI app serving templates for AI chat and diaries.",
    version="1.0.0",
)

# templates directory
templates = Jinja2Templates(directory="test_app/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    u = _load_user_context()

    # read latest defaults from YAML each request
    api_base, api_endpoint = _get_web_defaults()

    context = {
        "request": request,
        "current_user_name": u.get("name"),
        "current_user_email": u.get("email"),
        "current_user_id": u.get("id"),
        "current_user_farm_id": u.get("farm_id"),
        "current_user_location": u.get("location"),
        "current_user_location_name": u.get("location_name"),
        # injected config values for client JS
        "api_base_url": api_base,
        "api_endpoint": api_endpoint,
    }
    print('context:', context)
    return templates.TemplateResponse("index.html", context)


@app.get("/info", response_class=HTMLResponse)
async def info(request: Request):
    u = _load_user_context()
    api_base, api_endpoint = _get_web_defaults()

    context = {
        "request": request,
        "current_user_name": u.get("name"),
        "current_user_email": u.get("email"),
        "current_user_id": u.get("id"),
        "current_user_farm_id": u.get("farm_id"),
        "current_user_location": u.get("location"),
        "current_user_location_name": u.get("location_name"),
        "api_base_url": api_base,
        "api_endpoint": api_endpoint,
    }
    print('context:', context)
    return templates.TemplateResponse("info.html", context)


@app.get("/settings_guide", response_class=HTMLResponse)
async def settings_guide(request: Request):
    u = _load_user_context()
    api_base, api_endpoint = _get_web_defaults()

    context = {
        "request": request,
        "current_user_name": u.get("name"),
        "current_user_email": u.get("email"),
        "current_user_id": u.get("id"),
        "current_user_farm_id": u.get("farm_id"),
        "current_user_location": u.get("location"),
        "current_user_location_name": u.get("location_name"),
        "api_base_url": api_base,
        "api_endpoint": api_endpoint,
    }
    print('context:', context)
    return templates.TemplateResponse("settings_guide.html", context)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the test_app FastAPI server.")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind (default: 0.0.0.0 or $HOST)")
    parser.add_argument("--port", type=int, default=int(8001), help="Port to bind (default: 8001 or $PORT)")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn reload (useful for development).")
    args = parser.parse_args()

    import uvicorn
    uvicorn.run("client_server:app", host=args.host, port=args.port, reload=args.reload)
# from flask import Flask, Blueprint, request, Response, stream_with_context
from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from starlette.responses import StreamingResponse
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse

import json
import os
import re
import traceback
from pathlib import Path

from dotenv import load_dotenv

from config.configs import web_config, llm_config, rag_config, util_config
from config.config_file_loader import ConfigYamlLoader
from utils.parsing import message_parsing
from web.stream import async_stream_generator, get_data_from_service #sync_stream_gen 
from llm.utils import get_llm
from routing.domain_router import query_domain_routing, get_domain_info

# Optional YAML support for reading/writing web_config.yaml
try:
    import yaml
except Exception:
    yaml = None  # safe-check later

from graphrag_lib.graphrag.query import cli
from graphrag_lib.graphrag.query.structured_search.local_search.system_prompt import (
    LOCAL_SEARCH_SYSTEM_PROMPT, LOCAL_SEARCH_SYSTEM_PROMPT_REF
)
from utils.sql_extraction.sql_extractor import sql_extraction
from utils.recommand_business_list.business_list_filter import business_list_filtering
from utils.farming_diary.farming_diary_utils import add_work as add_work_util
from utils.farming_diary.farming_diary_utils import delete_works_by_date as delete_works_by_date_util
from lance_db.FarmingLanceDBManager import FarmingLanceDBManager

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]


@router.get("/persons", response_class=JSONResponse)
async def list_persons(request: Request):
    db = getattr(request.app.state, "farming_db", None)
    if db is None:
        raise HTTPException(status_code=500, detail="Farming DB not initialized")
    try:
        persons = db.list_persons()
        print('persons:', persons)
        return persons
    except Exception as e:
        print('persons error:', e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all_works_dates", response_class=JSONResponse)
async def all_works_dates(request: Request, person: str):
    """
    Return distinct dates available for given person (strings).
    """
    db = getattr(request.app.state, "farming_db", None)
    if db is None:
        raise HTTPException(status_code=500, detail="Farming DB not initialized")
    try:
        sql = """
        SELECT DISTINCT date FROM records
        WHERE (person = ? OR pid = ? OR person_name = ?)
        ORDER BY date ASC
        """
        rows = db.sql_query(sql, (person, person, person))
        dates = [r["date"] for r in rows if r.get("date")]
        return dates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/works", response_class=JSONResponse)
async def get_works(request: Request, person: str, date: str):
    """
    Return rows for person & date (list of dicts).
    """
    db = getattr(request.app.state, "farming_db", None)
    if db is None:
        raise HTTPException(status_code=500, detail="Farming DB not initialized")
    try:
        sql = """
        SELECT * FROM records
        WHERE (person = ? OR pid = ? OR person_name = ?) AND date = ?
        ORDER BY mtime ASC
        """
        rows = db.sql_query(sql, (person, person, person, date))
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/person_user_config", response_class=JSONResponse)
async def person_user_config(request: Request, person: str):
    """
    Query params: person=<person_key>  (예: '1_taeyong')
    Returns normalized user info dict from FarmingLanceDBManager.get_person_user_info
    """
    db = getattr(request.app.state, "farming_db", None)
    try:
        if db is None:
            mgr = FarmingLanceDBManager()
            info = mgr.get_person_user_info(person)
            return JSONResponse(content=info)
        info = db.get_person_user_info(person)
        return JSONResponse(content=info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set_main_user", response_class=JSONResponse)
async def set_main_user(request: Request, payload: dict = Body(...)):
    """
    Expects JSON body: { "id": <id>, "name": "<name>" }
    Rewrites config/user_configs.py's main_user_id, main_user_name, main_user_config_path lines.
    Returns { ok: True/False, message: ... }
    """
    try:
        new_id = payload.get("id")
        new_name = payload.get("name")
        if new_id is None or new_name is None:
            raise HTTPException(status_code=400, detail="id and name required")

        this_file = Path(__file__).resolve()
        repo_root = None
        for p in [this_file] + list(this_file.parents):
            if (p / "config").exists():
                repo_root = p
                break
        if repo_root is None:
            try:
                repo_root = this_file.parents[2]
            except Exception:
                repo_root = this_file.parent

        cfg_path = repo_root / "config" / "user_configs.py"
        if not cfg_path.exists():
            msg = f"{cfg_path} not found"
            print("[set_main_user] ERROR:", msg)
            return JSONResponse(content={"ok": False, "message": msg}, status_code=500)

        text = cfg_path.read_text(encoding="utf-8")

        try:
            id_repr = repr(int(new_id))
        except Exception:
            id_repr = repr(new_id)
        name_repr = repr(str(new_name))

        # Use callable replacements to avoid ambiguous numeric backreference parsing
        def repl_id(match):
            return match.group(1) + id_repr

        text, n1 = re.subn(r'^(main_user_id\s*=\s*)(.*)$',
                           repl_id,
                           text, flags=re.MULTILINE)

        def repl_name(match):
            return match.group(1) + name_repr

        text, n2 = re.subn(r'^(main_user_name\s*=\s*)(.*)$',
                           repl_name,
                           text, flags=re.MULTILINE)

        new_config_path_line = f'main_user_config_path = os.path.join(main_user_base_url, f"{new_id}_{new_name}", "user_config.yaml")'

        def repl_path(match):
            return new_config_path_line

        text, n3 = re.subn(r'^(main_user_config_path\s*=\s*)(.*)$',
                           repl_path,
                           text, flags=re.MULTILINE)

        if (n1 + n2 + n3) == 0:
            m = re.search(r'^(main_user_base_url\s*=.*)$', text, flags=re.MULTILINE)
            insert_at = None
            if m:
                insert_at = m.end()
            if insert_at:
                insertion = f"\nmain_user_id = {id_repr}\nmain_user_name = {name_repr}\n{new_config_path_line}\n"
                text = text[:insert_at] + insertion + text[insert_at:]

        tmp_path = cfg_path.with_suffix('.tmp')
        tmp_path.write_text(text, encoding="utf-8")
        os.replace(str(tmp_path), str(cfg_path))

        print(f"[set_main_user] updated {cfg_path} (n_replacements: {n1},{n2},{n3})")
        return JSONResponse(content={"ok": True, "message": "user_configs.py updated", "replacements": {"id": n1, "name": n2, "path": n3}})
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        print("[set_main_user] EXCEPTION:", str(e))
        print(tb)
        return JSONResponse(content={"ok": False, "message": str(e), "traceback": tb}, status_code=500)


@router.post("/set_web_config", response_class=JSONResponse)
async def set_web_config(request: Request, payload: dict = Body(...)):
    """
    Write/update config/web_config.yaml with provided settings.
    Expects JSON body: { "base_server_address": "...", "base_endpoint": "..." }
    Returns JSON { ok: True/False, message: ..., details: {...} }
    """
    try:
        base = payload.get("base_server_address")
        endpoint = payload.get("base_endpoint")
        if base is None or endpoint is None:
            raise HTTPException(status_code=400, detail="base_server_address and base_endpoint required")

        this_file = Path(__file__).resolve()
        repo_root = None
        for p in [this_file] + list(this_file.parents):
            if (p / "config").exists():
                repo_root = p
                break
        if repo_root is None:
            try:
                repo_root = this_file.parents[2]
            except Exception:
                repo_root = this_file.parent

        cfg_path = repo_root / "config" / "web_config.yaml"
        if not cfg_path.exists():
            return JSONResponse(content={"ok": False, "message": f"{cfg_path} not found"}, status_code=500)

        if yaml is None:
            return JSONResponse(content={"ok": False, "message": "PyYAML not available on the server; cannot update web_config.yaml"}, status_code=500)

        raw = cfg_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            data = {}

        web = data.get('web') if isinstance(data.get('web'), dict) else {}
        web['base_server_address'] = base
        web['base_endpoint'] = endpoint
        data['web'] = web

        new_text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)

        tmp_path = cfg_path.with_suffix(".tmp")
        tmp_path.write_text(new_text, encoding="utf-8")
        os.replace(str(tmp_path), str(cfg_path))

        return JSONResponse(content={"ok": True, "message": "web_config.yaml updated", "details": {"base_server_address": base, "base_endpoint": endpoint}})
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        print("[set_web_config] EXCEPTION:", e)
        print(tb)
        return JSONResponse(content={"ok": False, "message": str(e), "traceback": tb}, status_code=500)


class AddWorkPayload(BaseModel):
    person: str = Field(..., description="사람 식별자 (예: '1_taeyong' 또는 '1' 또는 'taeyong')")
    date: str = Field(..., description="날짜 (YYYY-MM-DD)")
    time: str = Field(..., description="시간 (HH:MM)")
    content: str = Field(..., description="일지 내용")
    target_filename: Optional[str] = Field(None, description="특정 파일에 저장하고 싶을 때 파일명(옵션)")

@router.post("/add_work", response_class=JSONResponse)
async def add_work(request: Request, payload: AddWorkPayload):
    """
    Add a work entry to the farming diary DB.
    Resolves 'person' flexibly (folder id, pid, or name).
    """
    db = getattr(request.app.state, "farming_db", None)
    if db is None:
        raise HTTPException(status_code=500, detail="Farming DB not initialized")
    try:
        result = add_work_util(
            db=db,
            person_identifier=payload.person,
            date=payload.date,
            time_str=payload.time,
            content=payload.content,
            target_filename=payload.target_filename
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/works", response_class=JSONResponse)
async def delete_works_for_date(request: Request, person: str, date: str):
    """
    해당 사람/날짜의 모든 일지를 삭제합니다.
    실제 파일(log_{date}*.json) 및 DB(records/processed_files)를 정리합니다.
    """
    db = getattr(request.app.state, "farming_db", None)
    if db is None:
        raise HTTPException(status_code=500, detail="Farming DB not initialized")
    try:
        result = delete_works_by_date_util(db, person_identifier=person, date=date)
        if not result.get("ok", False):
            raise HTTPException(status_code=500, detail=result.get("error", "delete failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
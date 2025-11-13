# from flask import Flask, Blueprint, request, Response, stream_with_context
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from starlette.responses import StreamingResponse
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse

import json
import os
from dotenv import load_dotenv

from config.configs import web_config, llm_config, rag_config, util_config
from utils.parsing import message_parsing
from web.stream import async_stream_generator, get_data_from_service #sync_stream_gen 
from llm.utils import get_llm
from routing.domain_router import query_domain_routing, get_domain_info

from graphrag_lib.graphrag.query import cli
from graphrag_lib.graphrag.query.structured_search.local_search.system_prompt import (
    LOCAL_SEARCH_SYSTEM_PROMPT, LOCAL_SEARCH_SYSTEM_PROMPT_REF
)
from utils.sql_extraction.sql_extractor import sql_extraction
from utils.recommand_business_list.business_list_filter import business_list_filtering
from utils.farming_diary.farming_diary_utils import add_work as add_work_util
from utils.farming_diary.farming_diary_utils import delete_works_by_date as delete_works_by_date_util

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]

# def get_farming_db(request: Request):

#     db = getattr(request.app.state, "farming_db", None)
#     if db is None:
#         raise RuntimeError("Farming DB가 초기화되지 않았습니다.")
#     return db

# @router.post("/farming_test")
# async def farming_test(chat_req: ChatRequest):
#     print('')

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
        # Query distinct dates for that person
        # Note: person may be folder id like '1_taeyong' or short name; match on person/pid/person_name columns
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
        # result 예시: {"rec": {...}, "file": "/path/...", "ok": True, "error": None}
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
        # 삭제 결과를 그대로 반환하여 어떤 파일이 지워졌는지 확인 가능
        if not result.get("ok", False):
            raise HTTPException(status_code=500, detail=result.get("error", "delete failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
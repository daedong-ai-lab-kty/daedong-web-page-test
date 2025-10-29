# from flask import Flask, Blueprint, request, Response, stream_with_context
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from starlette.responses import StreamingResponse

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

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]

def get_farming_db(request: Request):

    db = getattr(request.app.state, "farming_db", None)
    if db is None:
        raise RuntimeError("Farming DB가 초기화되지 않았습니다.")
    return db

@router.post("/farming_test")
async def farming_test(chat_req: ChatRequest):
    print('')

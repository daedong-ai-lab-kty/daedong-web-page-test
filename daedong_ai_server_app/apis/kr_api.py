# from flask import Flask, Blueprint, request, Response, stream_with_context
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from starlette.responses import StreamingResponse
import json 

from config import WebConfig
from utils.parsing import message_parsing
from utils.web.stream import async_stream_generator, get_data_from_service #sync_stream_gen 

# kr_api_bp = Blueprint('kr_ai_server_test', __name__)
# print(" =>> kr_api.py: Blueprint 'kr_api_bp'가 정의되었습니다.")
router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]

# @kr_api_bp.route('/kr_ai_server_test', methods=['POST', 'OPTIONS'])
@router.post("/kr_ai_server_test")
async def kr_ai_server_test(chat_req: ChatRequest):

    # model = request.json.get("model")
    # messages = request.json.get("messages")
    model = chat_req.model
    messages = chat_req.messages
    
    print(f'Model: {model}')
    print(f'Messages: {messages}')

    user_input = message_parsing(messages, recent_message_num=2)
    print(f' ==> User input:\n{user_input}')
    
    # response = messages
    domain_info = "Test"

    async_data_stream = get_data_from_service()

    # return Response(stream_with_context(response), mimetype='text/event-stream'), 200
    # return StreamingResponse(sync_stream_gen(response), media_type='text/event-stream')
    return StreamingResponse(
        async_stream_generator(domain=domain_info, async_data_source=async_data_stream), 
        media_type='text/event-stream'
    )

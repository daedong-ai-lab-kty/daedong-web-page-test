# from flask import Flask, Blueprint, request, Response, stream_with_context
from fastapi import APIRouter, HTTPException
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
# def kr_ai_server_test(chat_req: ChatRequest):

    ## Messages
    # model = request.json.get("model")
    # messages = request.json.get("messages")
    model = chat_req.model
    messages = chat_req.messages
    
    print(f'Model: {model}')
    print(f'Messages: {messages}')

    ## Input parsing
    query = message_parsing(messages, recent_message_num=2)
    print(f' ==> Query:\n{query}')
    
    ## LLM
    load_dotenv()
    llm_config['llm']['api_key'] = os.getenv('token')
    # print(config['llm']['api_key'])
    
    llm = get_llm(llm_config)
    
    ## Routing
    domains = web_config.KR_DOMAINS
    domain_routing_response = query_domain_routing(query, domains, llm, llm_config)
    domain_info = get_domain_info(domain_routing_response)

    reference = domain_info['reference']
    root_folder = domain_info['root_folder']
    domain = domain_info['domain_routing_response']
    print(" - Selected Domain:", domain)

    ## Business Support
    if domain == '지원사업':
        sql_filter = sql_extraction(query, llm, llm_config)
        async_response_stream = await business_list_filtering(sql_filter, llm, llm_config, \
            stream=True, table_name=util_config.BUSINESS_LIST_TABLE_NAME, text_path=root_folder)

    ## RAG Searching
    elif root_folder is not None:

        config_path = f'{root_folder}/settings.yaml'
        data_path = None #None #root_folder #f'{root_folder}/output'
        search_method = rag_config.SEARCH_METHOD
        community_level = rag_config.COMMUNITY_LEVEL
        response_type = rag_config.RESPONSE_TYPE
        streaming = True
        context_info_flag = False
        
        if search_method == 'local':

            # stream_gen = cli.run_local_search(
            #     config_path,
            #     data_path,
            #     root_folder,
            #     community_level,
            #     response_type,
            #     streaming,
            #     query,
            #     context_info_flag = context_info_flag,
            #     system_prompt = LOCAL_SEARCH_SYSTEM_PROMPT,
            # )
            async_response_stream = await cli.run_local_search(
                config_path,
                data_path,
                root_folder,
                community_level,
                response_type,
                streaming,
                query, 
                context_info_flag = context_info_flag,
                system_prompt = LOCAL_SEARCH_SYSTEM_PROMPT,
            )
            
        # if search_method == 'global':
        #     response, context_data = cli.run_global_search(
        #         config_path,
        #         data_path,
        #         root_folder,
        #         community_level,
        #         response_type,
        #         streaming,
        #         query,
            
    # else:

    #     llm_config['llm']['model'] = 'gpt-4.1'
    #     llm = get_llm(llm_config)

    #     sync_llm_stream = llm.generate(
    #         messages=[
    #             # {"role": "system", "content": query},
    #             {"role": "user", "content": query},
    #         ],
    #         streaming=True, 
    #         callbacks=None,
    #         model=llm_config['llm']['model'],
    #         temperature=llm_config['llm']['temperature'],
    #         max_tokens=llm_config['llm']['max_tokens'],
    #         top_p=llm_config['llm']['top_p']
    #         # **config['llm'],
    #     )

    # # 새로운 래퍼(wrapper) 제너레이터 정의
    # async def final_stream_wrapper(source_stream):
    #     # 원래 스트림에서 모든 데이터를 그대로 전달
    #     async for item in source_stream:
    #         yield item
    #     # 원래 스트림이 끝나면 'END!' 신호를 추가
    #     yield 'END!'

    # # 래퍼를 사용해 최종 스트림을 만듦
    # async_rag_stream = final_stream_wrapper(sync_llm_stream)
    
    ## Dummy
    # response = messages
    # domain = "Test"
    # async_data_stream = get_data_from_service()
    
    # return Response(stream_with_context(response), mimetype='text/event-stream'), 200
    # return StreamingResponse(sync_stream_gen(response), media_type='text/event-stream')
    return StreamingResponse(
        async_stream_generator(reference=reference, async_data_source=async_response_stream), 
        media_type='text/event-stream'
    )

@router.post("/kr_ai_server")
async def kr_ai_server(chat_req: ChatRequest):
# def kr_ai_server_test(chat_req: ChatRequest):

    ## Messages
    # model = request.json.get("model")
    # messages = request.json.get("messages")
    model = chat_req.model
    messages = chat_req.messages
    
    print(f'Model: {model}')
    print(f'Messages: {messages}')

    ## Input parsing
    query = message_parsing(messages, recent_message_num=2)
    print(f' ==> Query:\n{query}')
    
    ## LLM
    load_dotenv()
    llm_config['llm']['api_key'] = os.getenv('token')
    # print(config['llm']['api_key'])
    
    llm = get_llm(llm_config)
    
    ## Routing
    domains = web_config.KR_DOMAINS
    domain_routing_response = query_domain_routing(query, domains, llm, llm_config)
    domain_info = get_domain_info(domain_routing_response)

    reference = domain_info['reference']
    root_folder = domain_info['root_folder']
    domain = domain_info['domain_routing_response']
    print(" - Selected Domain:", domain)

    ## Business Support
    if domain == '지원사업':
        sql_filter = sql_extraction(query, llm, llm_config)
        async_response_stream = await business_list_filtering(sql_filter, llm, llm_config, \
            stream=True, table_name=util_config.BUSINESS_LIST_TABLE_NAME, text_path=root_folder)

    ## RAG Searching
    elif root_folder is not None:

        config_path = f'{root_folder}/settings.yaml'
        data_path = None #None #root_folder #f'{root_folder}/output'
        search_method = rag_config.SEARCH_METHOD
        community_level = rag_config.COMMUNITY_LEVEL
        response_type = rag_config.RESPONSE_TYPE
        streaming = True
        context_info_flag = False
        
        if search_method == 'local':

            # stream_gen = cli.run_local_search(
            #     config_path,
            #     data_path,
            #     root_folder,
            #     community_level,
            #     response_type,
            #     streaming,
            #     query,
            #     context_info_flag = context_info_flag,
            #     system_prompt = LOCAL_SEARCH_SYSTEM_PROMPT,
            # )
            async_response_stream = await cli.run_local_search(
                config_path,
                data_path,
                root_folder,
                community_level,
                response_type,
                streaming,
                query, 
                context_info_flag = context_info_flag,
                system_prompt = LOCAL_SEARCH_SYSTEM_PROMPT,
            )
            
        # if search_method == 'global':
        #     response, context_data = cli.run_global_search(
        #         config_path,
        #         data_path,
        #         root_folder,
        #         community_level,
        #         response_type,
        #         streaming,
        #         query,
            
    # else:

    #     llm_config['llm']['model'] = 'gpt-4.1'
    #     llm = get_llm(llm_config)

    #     sync_llm_stream = llm.generate(
    #         messages=[
    #             # {"role": "system", "content": query},
    #             {"role": "user", "content": query},
    #         ],
    #         streaming=True, 
    #         callbacks=None,
    #         model=llm_config['llm']['model'],
    #         temperature=llm_config['llm']['temperature'],
    #         max_tokens=llm_config['llm']['max_tokens'],
    #         top_p=llm_config['llm']['top_p']
    #         # **config['llm'],
    #     )

    # # 새로운 래퍼(wrapper) 제너레이터 정의
    # async def final_stream_wrapper(source_stream):
    #     # 원래 스트림에서 모든 데이터를 그대로 전달
    #     async for item in source_stream:
    #         yield item
    #     # 원래 스트림이 끝나면 'END!' 신호를 추가
    #     yield 'END!'

    # # 래퍼를 사용해 최종 스트림을 만듦
    # async_rag_stream = final_stream_wrapper(sync_llm_stream)
    
    ## Dummy
    # response = messages
    # domain = "Test"
    # async_data_stream = get_data_from_service()
    
    # return Response(stream_with_context(response), mimetype='text/event-stream'), 200
    # return StreamingResponse(sync_stream_gen(response), media_type='text/event-stream')
    return StreamingResponse(
        async_stream_generator(reference=reference, async_data_source=async_response_stream), 
        media_type='text/event-stream'
    )

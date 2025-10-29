import json
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import os
import argparse

from config.configs import web_config, llm_config, rag_config, util_config
from llm.utils import get_llm
from utils.farming_diary.farming_diary_builder_prompt import get_farming_diary_builder_prompt

def get_args():
    """
    커맨드 라인 인자(Arguments)를 파싱하여 반환합니다.
    """
    parser = argparse.ArgumentParser(
        description="영농일지 파일을 처리하는 RAG 스크립트"
    )

    parser.add_argument(
        '-f', '--file',
        dest='file_path',  # args.file_path 로 접근 가능
        required=True,
        type=str,
        help="처리할 영농일지 파일의 전체 경로 (예: /path/to/영농일지_10.docx)",
        metavar="FILE_PATH"
    )

    args = parser.parse_args()
    return args

def build_framing_daiary():

    ## LLM
    load_dotenv()
    llm_config['llm']['api_key'] = os.getenv('token')
    # print(config['llm']['api_key'])
    
    llm = get_llm(llm_config)

    farming_diary_builder_prompt = get_farming_diary_builder_prompt()

    farming_diary_builder_response = llm.generate(
    messages=[
            # {"role": "system", "content": routing_system_prompt},
            {"role": "user", "content": farming_diary_builder_prompt},
        ],
        streaming=True, 
        model=llm_config['llm']['model'],
        temperature=llm_config['llm']['temperature'],
        max_tokens=llm_config['llm']['max_tokens'],
        top_p=llm_config['llm']['top_p']
        # **config['llm'],
    )

    print(farming_diary_builder_response)

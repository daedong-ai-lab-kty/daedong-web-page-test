from typing import Dict
import os

from config.configs import web_config, llm_config, rag_config

def get_domain_query_routing_prompt(current_question, domains, language='Korean'):
    
    system_prompt = (
        "당신은 사용자의 질문을 분석하여 주어진 도메인 목록 중 가장 적합한 하나로 분류하는 전문 라우터입니다. "
    )

    user_prompt = f"""
    사용자의 질문을 아래 도메인 목록 중에서 가장 관련성이 높은 하나로 분류해주세요.

    [질문]
    "{current_question}"
    
    [도메인 목록]
    {domains}

    [출력 형식]
    관련성이 가장 높은 도메인을 쌍따옴표나 따옴표는 포함시키지 말고 [도메인 목록]에 있는 철자 그대로 출력해줘. 
    """

    return system_prompt, user_prompt
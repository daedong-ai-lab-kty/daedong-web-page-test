from typing import Dict
import os

from config.configs import web_config, llm_config, rag_config

def query_domain_routing(query, domains, llm, llm_config):

    routing_system_prompt, routing_user_prompt = get_domain_query_routing_prompt(current_question=query, \
        domains=domains)
    print('Routing user prompt:', routing_user_prompt)
    
    domain_routing_response = llm.generate(
        messages=[
            # {"role": "system", "content": routing_system_prompt},
            {"role": "user", "content": routing_user_prompt},
        ],
        streaming=False, 
        callbacks=None,
        model=llm_config['llm']['model'],
        temperature=llm_config['llm']['temperature'],
        max_tokens=llm_config['llm']['max_tokens'],
        top_p=llm_config['llm']['top_p']
        # **config['llm'],
    )

    print('Domain routing:', domain_routing_response)
    return domain_routing_response

def get_domain_query_routing_prompt(current_question, domains, language='Korean'):
    print(domains)
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

def get_domain_info(domain_routing_response):

    domain_info = {}

    root_folder = web_config.DOMAIN_TO_FOLDER_MAP[domain_routing_response]
    reference = web_config.DOMAIN_TO_REFERENCE_MAP[domain_routing_response]

    domain_info['domain_routing_response'] = domain_routing_response
    domain_info['root_folder'] = root_folder
    domain_info['reference'] = reference

    print(' == Domain Info ==')
    print(domain_info)

    return domain_info

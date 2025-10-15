from typing import Dict
import os

from config.configs import web_config, llm_config, rag_config
from routing.routing_prompt import get_domain_query_routing_prompt

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

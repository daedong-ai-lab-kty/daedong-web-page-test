import json
from datetime import datetime
import pandas as pd

from utils.sql_extraction.sql_extraction_prompt import get_business_list_sql_extraction_prompt, get_business_list_sql_extraction_prompt

def sql_extraction(query, llm, llm_config, text_path=None, verbose=False):

    current_date = datetime.now().strftime('%Y-%m-%d')
    sql_extraction_prompt = get_business_list_sql_extraction_prompt().format(
        current_date=current_date, user_query=query
    )

    if verbose:
        print('SQL Extraction prompt:', sql_extraction_prompt)
    
    # sql_extraction_prompt = [
    #     {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
    #     {"role": "user", "content": sql_extraction_prompt}
    # ]

    sql_extraction_response = llm.generate(
        messages=[
            # {"role": "system", "content": routing_system_prompt},
            {"role": "user", "content": sql_extraction_prompt},
        ],
        streaming=False, 
        callbacks=None,
        model=llm_config['llm']['model'],
        temperature=llm_config['llm']['temperature'],
        max_tokens=llm_config['llm']['max_tokens'],
        top_p=llm_config['llm']['top_p']
        # **config['llm'],
    )
    # print('sql_extraction_response:', sql_extraction_response)

    start_index = sql_extraction_response.find('{')
    end_index = sql_extraction_response.rfind('}') + 1
    if start_index != -1 and end_index != 0:
        sql_extraction_response = sql_extraction_response[start_index:end_index]

    sql_filter = json.loads(sql_extraction_response)['sql_where_clause']
    print(' - SQL Filter:', sql_filter)

    return sql_filter

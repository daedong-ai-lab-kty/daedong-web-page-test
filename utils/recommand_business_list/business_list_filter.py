import json
import pandas as pd
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from lance_db.LanceDB import LanceDB
from utils.recommand_business_list.business_list_filter_prompt import get_business_list_filter_prompt
from web.stream import sync_to_async_gen
from config.configs import web_config, llm_config, rag_config, util_config

async def business_list_filtering(sql_filter, llm, llm_config, \
    stream=True, table_name="knowledge_base", text_path=None):

    if text_path is not None:
        with open(text_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

    list_data = data['list']
    support_project_df = pd.DataFrame(list_data)
    # print(support_project_df.columns, support_project_df.head())

    ## DB init
    root_folder_path = web_config.RAG_DB_ROOT_PATH #'db_root_folder'
    # if not os.path.isfile(root_folder_path):
    db_instance = LanceDB(root_folder_path=root_folder_path)

    ## Generate DB
    my_table = db_instance.create_or_open_table(table_name, df=support_project_df, overwrite=True)
    # my_table.create_index() # 필요시 인덱스 생성

    ## SQL filter
    # filter = "date >= '2025-08-05'"
    results = db_instance.filter_sql(filter=sql_filter)
    subset = results[['title', 'content', 'applicant_type_nm', 'request_fr_date', 'request_to_date', 'institution_charge']]
    print("\n--- SQL Results ---")
    print(subset.head())
    # print(subset['request_fr_date'], subset['request_to_date'])
    # print(results)

    ## Business list filter
    subset['request_fr_date'] = subset['request_fr_date'].astype(str)
    subset['request_to_date'] = subset['request_to_date'].astype(str)
    sql_results_str = subset.head().to_string(index=False)

    business_list_filter_prompt = get_business_list_filter_prompt()

    business_list_filter_prompt = business_list_filter_prompt.format(
        sql_results=sql_results_str #str(subset.head())
    )
    # print('business_list_filter_prompt:', business_list_filter_prompt)

    if stream:

        callback_handler = StreamingStdOutCallbackHandler()
        business_list_filtering_response = llm.generate(
            messages=[
                    # {"role": "system", "content": routing_system_prompt},
                    {"role": "user", "content": business_list_filter_prompt},
                ],
            streaming=True, 
            callbacks=[callback_handler],
            model=llm_config['llm']['model'],
            temperature=llm_config['llm']['temperature'],
            max_tokens=llm_config['llm']['max_tokens'],
            top_p=llm_config['llm']['top_p']
            # **config['llm'],
        )
        async_response_stream = sync_to_async_gen(business_list_filtering_response)

        return async_response_stream

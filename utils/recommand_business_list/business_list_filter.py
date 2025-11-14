import json
import asyncio
import pandas as pd
from typing import Any

from web.stream import sync_to_async_gen
from config.configs import web_config, llm_config, rag_config, util_config
from utils.recommand_business_list.business_list_filter_prompt import get_business_list_filter_prompt

# Try to import a proper callback base if available (langchain_core)
try:
    from langchain_core.callbacks.base import BaseCallbackHandler
except Exception:
    try:
        from langchain.callbacks.base import BaseCallbackHandler
    except Exception:
        BaseCallbackHandler = object  # fallback


# This function returns an async iterable when stream=True.
# It pushes streaming tokens into an asyncio.Queue via a callback handler and
# returns an async generator that yields tokens as they arrive, so the web UI
# can show tokens immediately.
async def business_list_filtering(sql_filter: str, llm: Any, llm_config: dict,
                                  stream: bool = True, table_name: str = "knowledge_base", text_path: str = None):

    # load input data
    data = {}
    if text_path is not None:
        with open(text_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

    list_data = data.get('list', [])
    support_project_df = pd.DataFrame(list_data)

    # DB init
    root_folder_path = web_config.RAG_DB_ROOT_PATH
    from lance_db.LanceDB import LanceDB
    db_instance = LanceDB(root_folder_path=root_folder_path)

    # Generate DB table
    my_table = db_instance.create_or_open_table(table_name, df=support_project_df, overwrite=True)

    # SQL filter
    results = db_instance.filter_sql(filter=sql_filter)
    subset = results[['title', 'content', 'applicant_type_nm', 'request_fr_date', 'request_to_date', 'institution_charge']]

    # Prepare prompt
    subset['request_fr_date'] = subset['request_fr_date'].astype(str)
    subset['request_to_date'] = subset['request_to_date'].astype(str)
    sql_results_str = subset.head().to_string(index=False)

    business_list_filter_prompt = get_business_list_filter_prompt().format(sql_results=sql_results_str)

    # Non-streaming: return a final result (string)
    if not stream:
        resp = llm.generate(
            messages=[{"role": "user", "content": business_list_filter_prompt}],
            streaming=False,
            model=llm_config['llm']['model'],
            temperature=llm_config['llm']['temperature'],
            max_tokens=llm_config['llm']['max_tokens'],
            top_p=llm_config['llm']['top_p'],
        )
        if asyncio.iscoroutine(resp):
            resp = await resp
        return str(resp)

    # STREAMING: build a queue and a callback handler that pushes tokens into it
    queue: asyncio.Queue = asyncio.Queue()
    DONE = object()

    # Define a simple callback handler compatible with langchain callback interface.
    # We try to inherit BaseCallbackHandler if available (for better compatibility).
    class QueueCallbackHandler(BaseCallbackHandler):
        def __init__(self, q: asyncio.Queue):
            try:
                super().__init__()
            except Exception:
                pass
            self.q = q

        # langchain v0.0-like hook for new LLM token
        def on_llm_new_token(self, token: str, **kwargs):
            try:
                # put token without blocking current sync thread
                self.q.put_nowait(token)
            except Exception:
                # if queue is full or closed, ignore
                pass

        # For some callback APIs the method name is different; provide alias
        def on_new_token(self, token: str, **kwargs):
            try:
                self.q.put_nowait(token)
            except Exception:
                pass

        # Called when LLM stream ends
        def on_llm_end(self, **kwargs):
            try:
                self.q.put_nowait(DONE)
            except Exception:
                pass

        # alias for other callback signatures
        def on_chain_end(self, **kwargs):
            try:
                self.q.put_nowait(DONE)
            except Exception:
                pass

    handler = QueueCallbackHandler(queue)

    # Runner to invoke llm.generate in a thread to avoid blocking event loop.
    # We will not await it here (it will run concurrently), the callback will feed the queue.
    def run_generate():
        try:
            # many LLMs expect sync call; pass our handler as callback
            llm.generate(
                messages=[{"role": "user", "content": business_list_filter_prompt}],
                streaming=True,
                callbacks=[handler],
                model=llm_config['llm']['model'],
                temperature=llm_config['llm']['temperature'],
                max_tokens=llm_config['llm']['max_tokens'],
                top_p=llm_config['llm']['top_p'],
            )
        except Exception as e:
            # push error information to queue for debugging and termination
            try:
                queue.put_nowait(f"[ERROR in llm.generate] {e}")
            except Exception:
                pass
            try:
                queue.put_nowait(DONE)
            except Exception:
                pass

    loop = asyncio.get_running_loop()
    gen_future = loop.run_in_executor(None, run_generate)

    # async generator that yields tokens from the queue as they arrive
    async def _stream_gen():
        try:
            while True:
                item = await queue.get()
                if item is DONE:
                    break
                # If the handler pushed JSON-like chunks or dicts, convert to string as needed
                yield item
        finally:
            # ensure the generate thread has finished (wait for it)
            try:
                await gen_future
            except Exception as e:
                # log but don't crash the generator
                print("[business_list_filtering] llm.generate raised in executor:", e)

    return _stream_gen()
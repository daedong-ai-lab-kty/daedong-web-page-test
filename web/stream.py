
import asyncio
import datetime
import json
import time

async def sync_to_async_gen(sync_gen):
    for chunk in sync_gen:
        yield chunk
        await asyncio.sleep(0)

    yield 'END!'
    await asyncio.sleep(0)

async def get_data_from_service():
    for i in range(5):
        yield f"데이터 청크 {i} "
        await asyncio.sleep(0.2)
    yield "END!"

async def async_stream_generator(reference: str, async_data_source):
    """
    FastAPI StreamingResponse에 맞는 비동기 제너레이터.
    SSE(Server-Sent Events) 형식으로 데이터를 yield합니다.
    """
    try:
        # 첫 번째 청크를 먼저 보냄 (OpenAI API 호환 형식)
        initial_chunk = { "id": 'chatcmpl-RAG', "object": "chat.completion.chunk", "created": int(time.time()), "model": 'RAG', "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}] }
        yield f"data: {json.dumps(initial_chunk, ensure_ascii=False)}\n\n"

        buffer = ""
        # 비동기 데이터 소스를 async for로 직접 순회
        async for data in async_data_source:
            print(' - Data:', data)

            if data == 'END!':
                # 루프 종료 전 버퍼에 남은 데이터 전송
                if buffer:
                    chunk = { "id": 'chatcmpl-RAG', "object": "chat.completion.chunk", "created": int(time.time()), "model": 'RAG', "choices": [{"index": 0, "delta": {"content": buffer}, "finish_reason": None}] }
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                
                # 참조 정보 전송
                if reference is not None:
                    ref_chunk = { "id": 'chatcmpl-RAG', "object": "chat.completion.chunk", "created": int(time.time()), "model": 'RAG', "choices": [{"index": 0, "delta": {"content": f"\n\n참조: {reference}"}, "finish_reason": None}] }
                    yield f"data: {json.dumps(ref_chunk, ensure_ascii=False)}\n\n"
                
                # 종료 청크 전송
                end_chunk = { "id": 'chatcmpl-RAG', "object": "chat.completion.chunk", "created": int(time.time()), "model": 'RAG', "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}] }
                yield f"data: {json.dumps(end_chunk, ensure_ascii=False)}\n\n"
                break
            else:
                buffer += str(data)
                # 버퍼가 일정 크기 이상이면 전송 (또는 개행 문자 기준 등)
                if len(buffer) >= 4:
                    chunk = { "id": 'chatcmpl-RAG', "object": "chat.completion.chunk", "created": int(time.time()), "model": 'RAG', "choices": [{"index": 0, "delta": {"content": buffer}, "finish_reason": None}] }
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    buffer = ""
        
        # [DONE] 메시지로 스트림 완전 종료 신호 전송
        yield "data: [DONE]\n\n"

    except Exception as e:
        print(f"스트리밍 중 오류 발생: {e}")

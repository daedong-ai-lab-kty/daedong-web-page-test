import datetime
import json
import time

def message_parsing(messages, recent_message_num=1):

    recent_messages = [
        {"role": message.role, "content": message.content}
        for message in messages if message.role in ["user", "assistant"]
    ][-recent_message_num:]

    formatted_messages = json.dumps(recent_messages, ensure_ascii=False)
    
    return formatted_messages
    



from pydantic import BaseModel, Field
import uvicorn
import argparse
from typing import Dict
import os

from daedong_ai_server_app import create_app

## Env variable
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
PUBLIC_IP = os.getenv('PUBLIC_IP', None)

daedong_ai_server_app = create_app(PUBLIC_IP, HOST, PORT)

if __name__ == "__main__":
    print(f"Starting server on {HOST}:{PORT}")
    uvicorn.run(daedong_ai_server_app, host=HOST, port=PORT)
    
    
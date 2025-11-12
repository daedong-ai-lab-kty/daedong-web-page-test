from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# FastAPI 앱
app = FastAPI(
    title="AI Chat Assistant",
    description="Simple FastAPI app serving templates for AI chat and diaries.",
    version="1.0.0",
)

# 정적 파일이 있다면 사용 (없으면 주석 처리해도 됨)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# 템플릿 디렉토리 설정
templates = Jinja2Templates(directory="test_app/templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/info", response_class=HTMLResponse)
async def info(request: Request):
    return templates.TemplateResponse("info.html", {"request": request})

@app.get("/settings_guide", response_class=HTMLResponse)
async def settings_guide(request: Request):
    return templates.TemplateResponse("settings_guide.html", {"request": request})

# uvicorn 실행 진입점
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("client_server:app", host="0.0.0.0", port=8559, reload=True)
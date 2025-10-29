import socket
import threading
import os 
from pathlib import Path
import time

# from flask import Flask
# from flask_cors import CORS
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config.configs import web_config, llm_config, rag_config, util_config
from lance_db.FarmingLanceDBManager import FarmingLanceDBManager
from utils.farming_diary.farming_diary_utils import get_persons, get_all_works_date, get_search_works, add_work

def create_app(PUBLIC_IP, HOST, PORT):
    # app = Flask(__name__)
    app = FastAPI()

    # CORS(app, resources={r"/*": {"origins": "*"}})
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], 
        allow_credentials=True,
        allow_methods=["*"],  
        allow_headers=["*"], 
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_ts = time.time()
        client = request.client.host if request.client else "unknown"
        try:
            # request.url includes path + query params
            url = str(request.url)
        except Exception:
            url = request.url.path
        # read body safely (body can be consumed once; some endpoints may not expect us to read it)
        try:
            body = await request.body()
            # limit body logged length
            body_preview = body[:1000] if body else b''
        except Exception:
            body_preview = b''
        print(f'--> {client} {request.method} {url}')
        if body_preview:
            try:
                # try to decode for readable print; fall back to bytes repr
                print(f'    Body: {body_preview.decode(errors="replace")}')
            except Exception:
                print(f'    Body (bytes): {body_preview!r}')
        # call downstream handler
        response = await call_next(request)
        duration_ms = (time.time() - start_ts) * 1000
        print(f'<-- {request.method} {url} {response.status_code} ({duration_ms:.1f} ms)')
        return response

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
    except Exception:
        ip_address = "127.0.0.1"
        print("외부 IP 주소를 찾을 수 없습니다. 로컬 주소로 서버를 시작합니다.")
    
    print("=" * 60)
    print("FastAPI 서버를 시작합니다. 다른 기기에서 접속하여 테스트하세요.")
    print(f"   - 로컬 접속: http://127.0.0.1:{PORT}")
    print(f"   - 외부 접속 (Docker IP): http://{ip_address}:{PORT}")
    if PUBLIC_IP is not None:
        print(f"   - 외부 접속 (Public IP): http://{PUBLIC_IP}:{PORT}")
    print(f"   - API 문서 (Swagger UI): http://{ip_address}:{PORT}/docs")
    print("=" * 60)
    print("서버를 중지하려면 CTRL+C를 누르세요.")

    # 여기에 설정 로드, DB 초기화 등 공통 작업 수행
    # 예: app.config.from_object('config.Config')
    
    # Blueprint 등록
    # from .apis.kr_api import kr_api_bp
    # from .apis.eu_na_api import eu_na_api_bp
    from .apis.kr_api import router as kr_router
    from .apis.farming_api import router as farming_router
    # app.register_blueprint(kr_api_bp)
    # app.include_router(kr_router, prefix="/api")
    app.include_router(kr_router)
    app.include_router(farming_router)
    # app.register_blueprint(eu_na_api_bp)
    
    @app.on_event("startup")
    async def startup_event():
        # 생성 비용이 있는 리소스는 startup에서 초기화
        db_root = web_config.DOMAIN_TO_FOLDER_MAP['영농일지']
        app.state.farming_db = FarmingLanceDBManager(root_dir=db_root, use_openai=False)
        db = app.state.farming_db
        
        def db_ingest():
            try:
                print(" => Starting ingest_from_server ...")
                db.ingest_from_server(db_root)
                print(" => ingest_from_server finished.")

                # print(" => After ingest, tables:")
                
                # date = '2023-09-25'
                # time = '15:30'
                # content = '새 작업 내역 예시'
                # folder = '1_taeyong' #os.path.join(db_root, '1_taeyong')
                # add_work(db, folder, date, time, content)

                # works1 = get_all_works_date(db, 'taeyong', '2023-09-22')
                # # print(' - Works1:', works1)

                # works2 = get_all_works_date(db, 'taeyong', '2023-09-25')
                # print(' - Works2:', works2)

            except Exception as e:
                print("ingest error:", e)

        # 데몬 스레드로 백그라운드 ingest (서버 스타트업 블로킹하지 않음)
        threading.Thread(target=db_ingest, daemon=True).start()
        
        # folders = get_persons(db)
        # print('Folders:', folders)
        # db.print_all_tables()
        # works = get_all_works_date(db, '1_taeyong', '2023-09-22')
        # print('Works:', works)
        # print(" ==> FarmingLanceDBManager 초기화 완료")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        db = getattr(app.state, "farming_db", None)
        if db is not None:
            close_fn = getattr(db, "close", None)
            if callable(close_fn):
                close_fn()
            print(" ==> FarmingLanceDBManager 정리 완료")
    
    @app.get("/")
    def read_root():
        print("Request received at root endpoint.")
        return {"status": "ok", "message": f"Hello from the server running on port {PORT}!"}
        
    # Farming DB
    # farming_db = FarmingLanceDBManager(root_dir=web_config.DOMAIN_TO_FOLDER_MAP['영농일지'], use_openai=False)
    # print("Persons:", farming_db.list_persons())
    
    return app
    
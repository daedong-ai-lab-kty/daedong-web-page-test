import socket

# from flask import Flask
# from flask_cors import CORS
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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

    # app.register_blueprint(kr_api_bp)
    # app.include_router(kr_router, prefix="/api")
    app.include_router(kr_router)
    # app.register_blueprint(eu_na_api_bp)
    
    @app.get("/")
    def read_root():
        print("Request received at root endpoint.")
        return {"status": "ok", "message": f"Hello from the server running on port {PORT}!"}

    return app

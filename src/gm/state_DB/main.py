# main.py - GTRPGM 상태 관리 FastAPI 서버

from fastapi import FastAPI

# 로컬 모듈 import
from .custom import CustomJSONResponse
from .Query.query import shutdown as db_shutdown
from .Query.query import startup as db_startup
from .router import state_router

# 설정값 (TODO: src/configs로 분리 가능)
APP_ENV = "local"
APP_PORT = 8000

# 로깅 설정
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "default": {"class": "logging.StreamHandler", "stream": "ext://sys.stdout"},
        "access": {"class": "logging.StreamHandler", "stream": "ext://sys.stdout"},
    },
    "loggers": {
        "uvicorn.error": {"level": "INFO", "handlers": ["default"]},
        "uvicorn.access": {"level": "INFO", "handlers": ["access"]},
    },
}


# ====================================================================
# FastAPI 앱 초기화
# ====================================================================

app = FastAPI(
    title="GTRPGM State Manager",
    description="TRPG 게임 상태를 관리하고 최신 상태를 제공하는 API",
    version="1.0.0",
    default_response_class=CustomJSONResponse,  # 모든 응답에 표준 포맷 적용
)


# ====================================================================
# 라우터 등록
# ====================================================================

# 상태 관리 관련 라우터 등록 (prefix로 /state 경로 추가)
app.include_router(state_router, prefix="/state", tags=["State Management"])

# 필요한 다른 라우터들 추가
# from src.other_module.routers import other_router
# app.include_router(other_router)


# ====================================================================
# 앱 생명주기 이벤트
# ====================================================================


@app.on_event("startup")
async def on_startup():
    """서버 시작 시 DB 연결 풀 초기화"""
    await db_startup()


@app.on_event("shutdown")
async def on_shutdown():
    """서버 종료 시 DB 연결 풀 정리"""
    await db_shutdown()


# ====================================================================
# 루트 엔드포인트
# ====================================================================


@app.get("/", description="서버 연결 확인", summary="테스트 - 서버 연결을 확인합니다.")
def read_root():
    """서버 상태 확인용 루트 엔드포인트"""
    return {
        "message": "반갑습니다. GTRPGM 상태 관리자입니다!",
        "service": "State Manager",
        "version": "1.0.0",
    }


@app.get("/health", description="헬스체크", summary="서버 헬스체크")
async def health_check():
    """헬스체크 엔드포인트 (로드밸런서/모니터링용)"""
    return {"status": "healthy"}


# ====================================================================
# 서버 실행 (개발 환경)
# ====================================================================

if __name__ == "__main__":
    import uvicorn

    # 로컬 환경에서는 127.0.0.1, 배포 환경에서는 0.0.0.0
    effective_host = "127.0.0.1" if APP_ENV == "local" else "0.0.0.0"

    # 로깅 핸들러 스트림 설정 (stdout으로 통일)
    LOGGING_CONFIG["handlers"]["default"]["stream"] = "ext://sys.stdout"
    LOGGING_CONFIG["handlers"]["access"]["stream"] = "ext://sys.stdout"

    # uvicorn 서버 실행
    uvicorn.run(
        "main:app",
        host=effective_host,
        port=APP_PORT,
        reload=(APP_ENV == "local"),  # 로컬 환경에서만 auto-reload
        log_config=LOGGING_CONFIG,
    )
